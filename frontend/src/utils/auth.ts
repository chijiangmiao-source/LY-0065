export const getToken = () => localStorage.getItem('token')

export const setToken = (token: string) => localStorage.setItem('token', token)

export const removeToken = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
}

export const isAuthenticated = () => !!getToken()

export const setUsername = (username: string) => localStorage.setItem('username', username)

export const getUsername = () => localStorage.getItem('username')
