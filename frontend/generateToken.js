import jwt from 'jsonwebtoken'
import fs from 'fs'

// Load credentials securely
const teamId = process.env.APPLE_MUSIC_TEAM_ID // From Render Env Variables
const keyId = process.env.APPLE_MUSIC_KEY_ID // From Render Env Variables
const privateKey = fs.readFileSync('/etc/secrets/AuthKey.p8', 'utf8') // From Render Secret Files

// Generate JWT Token
const token = jwt.sign({}, privateKey, {
  algorithm: 'ES256',
  expiresIn: '180d', // Token valid for 180 days
  keyid: keyId,
  issuer: teamId,
})

console.log('Apple Music Developer Token:', token)
