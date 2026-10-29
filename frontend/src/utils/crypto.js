/**
 * 用后端下发的 RSA 公钥（SubjectPublicKeyInfo / PEM）加密密码。
 * 使用浏览器原生 WebCrypto 的 RSA-OAEP(SHA-256)，与后端 cryptography 的 OAEP 填充匹配。
 * 注意：WebCrypto 仅在安全上下文（https 或 localhost）可用。
 */
function pemToBuffer(pem) {
  const body = pem
    .replace('-----BEGIN PUBLIC KEY-----', '')
    .replace('-----END PUBLIC KEY-----', '')
    .replace(/\s/g, '')
  const binary = atob(body)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  return bytes.buffer
}

function bufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
  return btoa(binary)
}

export async function encryptPassword(plain, publicKeyPem) {
  if (!window.crypto || !window.crypto.subtle) {
    throw new Error('当前环境不支持安全加密（需 https 或 localhost）')
  }
  const key = await window.crypto.subtle.importKey(
    'spki',
    pemToBuffer(publicKeyPem),
    { name: 'RSA-OAEP', hash: 'SHA-256' },
    false,
    ['encrypt'],
  )
  const cipher = await window.crypto.subtle.encrypt(
    { name: 'RSA-OAEP' },
    key,
    new TextEncoder().encode(plain),
  )
  return bufferToBase64(cipher)
}
