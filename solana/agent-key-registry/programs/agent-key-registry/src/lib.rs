use anchor_lang::prelude::*;
use anchor_lang::solana_program::hash::hashv;
use anchor_lang::solana_program::ed25519_program;
use anchor_lang::solana_program::sysvar::instructions::{
    load_instruction_at_checked, ID as SYSVAR_INSTRUCTIONS_ID,
};

declare_id!("AgKyRgsTrY11111111111111111111111111111111");

#[program]
pub mod agent_key_registry {
    use super::*;

    pub fn register_key(
        ctx: Context<RegisterKey>,
        owner_agent_id: String,
        key_id: String,
        pubkey: [u8; 32],
    ) -> Result<()> {
        require!(
            !owner_agent_id.trim().is_empty() && !key_id.trim().is_empty(),
            ErrorCode::InvalidKeyIdentity
        );
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
        let key = &ctx.accounts.agent_key;
        require!(
            key.owner_agent_id == owner_agent_id && key.key_id == key_id,
            ErrorCode::InvalidKeyIdentity
        );
        require!(!key.revoked, ErrorCode::KeyRevoked);

        let ix = load_instruction_at_checked(
            signature_instruction_index as usize,
            &ctx.accounts.instructions.to_account_info(),
        )?;
        require_keys_eq!(ix.program_id, ed25519_program::id(), ErrorCode::SignatureMissing);
        require!(!message.is_empty(), ErrorCode::InvalidAttestationPayload);

        let run = &mut ctx.accounts.run_record;
        run.owner_agent_id = owner_agent_id;
        run.key_id = key_id;
        run.message_sha256 = hashv(&[message.as_slice()]).to_bytes();
        run.slot = Clock::get()?.slot;
        run.bump = ctx.bumps.run_record;
        Ok(())
    }
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
        seeds = [b"agent_key", owner_agent_id.as_bytes(), key_id.as_bytes()],
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
        seeds = [b"agent_key", owner_agent_id.as_bytes(), key_id.as_bytes()],
        bump = agent_key.bump
    )]
    pub agent_key: Account<'info, AgentKey>,
}

#[derive(Accounts)]
#[instruction(owner_agent_id: String, key_id: String, message: Vec<u8>)]
pub struct SubmitAttestation<'info> {
    #[account(
        seeds = [b"agent_key", owner_agent_id.as_bytes(), key_id.as_bytes()],
        bump = agent_key.bump
    )]
    pub agent_key: Account<'info, AgentKey>,
    #[account(
        init,
        payer = payer,
        space = 8 + RunRecord::SPACE,
        seeds = [b"run_record", owner_agent_id.as_bytes(), key_id.as_bytes(), hashv(&[message.as_slice()]).as_ref()],
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
    #[msg("Agent key has been revoked")]
    KeyRevoked,
    #[msg("Missing preceding ed25519 signature verification instruction")]
    SignatureMissing,
    #[msg("Invalid attestation payload")]
    InvalidAttestationPayload,
}
