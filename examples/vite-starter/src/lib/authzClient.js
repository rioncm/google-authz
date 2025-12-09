export async function checkPermission(baseUrl, permission, tokenType, tokenValue) {
  const [module, action] = permission.split(':')
  if (!module || !action) {
    throw new Error('Use module:action syntax (example inventory:read)')
  }
  if (!tokenValue) {
    throw new Error('Provide an id_token or session_token before evaluating permissions')
  }
  const payload = {
    module,
    action,
  }
  if (tokenType === 'id_token') {
    payload.id_token = tokenValue.trim()
  } else {
    payload.session_token = tokenValue.trim()
  }
  const response = await fetch(`${baseUrl}/authz/check`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Check failed (${response.status}) ${text}`)
  }
  return response.json()
}
