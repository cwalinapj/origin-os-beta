use anchor_lang::prelude::*;
use anchor_lang::solana_program::hash::hashv;
use anchor_lang::solana_program::ed25519_program;
use anchor_lang::solana_program::sysvar::instructions::{
    load_current_index_checked, load_instruction_at_checked, ID as SYSVAR_INSTRUCTIONS_ID,
};

declare_id!("AgKyRgsTrY11111111111111111111111111111111");
const MAX_ID_BYTES: usize = 128;

#[program]
pub mod agent_key_registry {
    use super::*;

    pub fn register_key(
        ctx: Context<RegisterKey>,
        owner_agent_id: String,
        key_id: String,
        pubkey: [u8; 32],
    ) -> Result<()> {
        require_valid_key_identity(&owner_agent_id, &key_id)?;
        let key = &mut ctx.accounts.agent_key;
        key.owner_agent_id = owner_agent_id;
        key.key_id = key_id;
        key.authority = ctx.accounts.authority.key();
        key.pubkey = pubkey;
        key.revoked = false;
        key.bump = ctx.bumps.agent_key;
        Ok(())
    }

    pub fn revoke_key(
        ctx: Context<RevokeKey>,
        owner_agent_id: String,
        key_id: String,
    ) -> Result<()> {
        require_valid_key_identity(&owner_agent_id, &key_id)?;
        let key = &mut ctx.accounts.agent_key;
        require!(
            key.owner_agent_id == owner_agent_id && key.key_id == key_id,
            ErrorCode::InvalidKeyIdentity
        );
        key.revoked = true;
        Ok(())
    }

    pub fn submit_attestation(
        ctx: Context<SubmitAttestation>,
        owner_agent_id: String,
        key_id: String,
        message: Vec<u8>,
        signature_instruction_index: u16,
    ) -> Result<()> {
        require_valid_key_identity(&owner_agent_id, &key_id)?;
        let key = &ctx.accounts.agent_key;
        require!(
            key.owner_agent_id == owner_agent_id && key.key_id == key_id,
            ErrorCode::InvalidKeyIdentity
        );
        require!(!key.revoked, ErrorCode::KeyRevoked);
        require!(!message.is_empty(), ErrorCode::InvalidAttestationPayload);

        let current_ix_index = load_current_index_checked(&ctx.accounts.instructions.to_account_info())?;
        let expected_sig_ix = current_ix_index
            .checked_sub(1)
            .ok_or_else(|| error!(ErrorCode::SignatureMissing))?;
        require!(
            signature_instruction_index as usize == expected_sig_ix,
            ErrorCode::SignatureMissing
        );

        let ix = load_instruction_at_checked(
            signature_instruction_index as usize,
            &ctx.accounts.instructions.to_account_info(),
        )?;
        require_keys_eq!(ix.program_id, ed25519_program::id(), ErrorCode::SignatureMissing);
        require_ed25519_verifies(&ix.data, signature_instruction_index, key.pubkey, &message)?;

        let run = &mut ctx.accounts.run_record;
        run.owner_agent_id = owner_agent_id;
        run.key_id = key_id;
        run.message_sha256 = hashv(&[message.as_slice()]).to_bytes();
        run.slot = Clock::get()?.slot;
        run.bump = ctx.bumps.run_record;
        Ok(())
    }
}

fn require_valid_key_identity(owner_agent_id: &str, key_id: &str) -> Result<()> {
    require!(
        !owner_agent_id.trim().is_empty() && !key_id.trim().is_empty(),
        ErrorCode::InvalidKeyIdentity
    );
    require!(
        owner_agent_id.as_bytes().len() <= MAX_ID_BYTES && key_id.as_bytes().len() <= MAX_ID_BYTES,
        ErrorCode::KeyIdentityTooLong
    );
    Ok(())
}

fn require_ed25519_verifies(
    ix_data: &[u8],
    signature_instruction_index: u16,
    expected_pubkey: [u8; 32],
    expected_message: &[u8],
) -> Result<()> {
    const ED25519_HEADER_LEN: usize = 16;
    const SIGNATURE_LEN: usize = 64;
    const PUBKEY_LEN: usize = 32;
    if ix_data.len() < ED25519_HEADER_LEN {
        return err!(ErrorCode::InvalidSignatureInstruction);
    }

    let num_signatures = ix_data[0];
    let padding = ix_data[1];
    require!(
        num_signatures == 1 && padding == 0,
        ErrorCode::InvalidSignatureInstruction
    );

    let signature_offset = read_u16_le(ix_data, 2)? as usize;
    let signature_instruction = read_u16_le(ix_data, 4)?;
    let pubkey_offset = read_u16_le(ix_data, 6)? as usize;
    let pubkey_instruction = read_u16_le(ix_data, 8)?;
    let message_offset = read_u16_le(ix_data, 10)? as usize;
    let message_size = read_u16_le(ix_data, 12)? as usize;
    let message_instruction = read_u16_le(ix_data, 14)?;

    // In the ed25519 instruction data layout, 0xFFFF means "current instruction index".
    // Valid references therefore point to either this instruction's index or the 0xFFFF sentinel.
    let is_current_instruction_or_max =
        |idx: u16| idx == u16::MAX || idx == signature_instruction_index;
    require!(
        is_current_instruction_or_max(signature_instruction)
            && is_current_instruction_or_max(pubkey_instruction)
            && is_current_instruction_or_max(message_instruction),
        ErrorCode::InvalidSignatureInstruction
    );
    require!(
        signature_offset + SIGNATURE_LEN <= ix_data.len(),
        ErrorCode::InvalidSignatureInstruction
    );
    require!(
        pubkey_offset + PUBKEY_LEN <= ix_data.len(),
        ErrorCode::InvalidSignatureInstruction
    );
    require!(
        message_offset + message_size <= ix_data.len(),
        ErrorCode::InvalidSignatureInstruction
    );

    let instruction_pubkey = &ix_data[pubkey_offset..pubkey_offset + PUBKEY_LEN];
    require!(
        instruction_pubkey == expected_pubkey.as_slice(),
        ErrorCode::InvalidSignatureInstruction
    );

    let instruction_message = &ix_data[message_offset..message_offset + message_size];
    require!(
        instruction_message == expected_message,
        ErrorCode::InvalidSignatureInstruction
    );
    Ok(())
}

fn read_u16_le(data: &[u8], offset: usize) -> Result<u16> {
    if offset + 2 > data.len() {
        return err!(ErrorCode::InvalidSignatureInstruction);
    }
    Ok(u16::from_le_bytes([data[offset], data[offset + 1]]))
}

#[derive(Accounts)]
#[instruction(owner_agent_id: String, key_id: String, _pubkey: [u8; 32])]
pub struct RegisterKey<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
    pub authority: Signer<'info>,
    #[account(
        init,
        payer = payer,
        space = 8 + AgentKey::SPACE,
        seeds = [
            b"agent_key",
            hashv(&[owner_agent_id.as_bytes()]).as_ref(),
            hashv(&[key_id.as_bytes()]).as_ref()
        ],
        bump
    )]
    pub agent_key: Account<'info, AgentKey>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(owner_agent_id: String, key_id: String)]
pub struct RevokeKey<'info> {
    pub authority: Signer<'info>,
    #[account(
        mut,
        has_one = authority,
        seeds = [
            b"agent_key",
            hashv(&[owner_agent_id.as_bytes()]).as_ref(),
            hashv(&[key_id.as_bytes()]).as_ref()
        ],
        bump = agent_key.bump
    )]
    pub agent_key: Account<'info, AgentKey>,
}

#[derive(Accounts)]
#[instruction(owner_agent_id: String, key_id: String, message: Vec<u8>)]
pub struct SubmitAttestation<'info> {
    #[account(
        seeds = [
            b"agent_key",
            hashv(&[owner_agent_id.as_bytes()]).as_ref(),
            hashv(&[key_id.as_bytes()]).as_ref()
        ],
        bump = agent_key.bump
    )]
    pub agent_key: Account<'info, AgentKey>,
    #[account(
        init,
        payer = payer,
        space = 8 + RunRecord::SPACE,
        seeds = [
            b"run_record",
            hashv(&[owner_agent_id.as_bytes()]).as_ref(),
            hashv(&[key_id.as_bytes()]).as_ref(),
            hashv(&[message.as_slice()]).as_ref()
        ],
        bump
    )]
    pub run_record: Account<'info, RunRecord>,
    #[account(mut)]
    pub payer: Signer<'info>,
    /// CHECK: validated by address constraint and used for instruction sysvar reads.
    #[account(address = SYSVAR_INSTRUCTIONS_ID)]
    pub instructions: UncheckedAccount<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct AgentKey {
    pub owner_agent_id: String,
    pub key_id: String,
    pub authority: Pubkey,
    pub pubkey: [u8; 32],
    pub revoked: bool,
    pub bump: u8,
}

impl AgentKey {
    const SPACE: usize = (4 + 128) + (4 + 128) + 32 + 32 + 1 + 1;
}

#[account]
pub struct RunRecord {
    pub owner_agent_id: String,
    pub key_id: String,
    pub message_sha256: [u8; 32],
    pub slot: u64,
    pub bump: u8,
}

impl RunRecord {
    const SPACE: usize = (4 + 128) + (4 + 128) + 32 + 8 + 1;
}

#[error_code]
pub enum ErrorCode {
    #[msg("owner_agent_id/key_id must be non-empty and match PDA")]
    InvalidKeyIdentity,
    #[msg("owner_agent_id/key_id exceed maximum supported size")]
    KeyIdentityTooLong,
    #[msg("Agent key has been revoked")]
    KeyRevoked,
    #[msg("Missing preceding ed25519 signature verification instruction")]
    SignatureMissing,
    #[msg("Invalid ed25519 signature verification instruction")]
    InvalidSignatureInstruction,
    #[msg("Invalid attestation payload")]
    InvalidAttestationPayload,
}
