import { useState } from 'react'
import { useForm } from 'react-hook-form'

import { useAuth } from '../../hooks/useAuth'
import { getApiErrorMessage } from '../../services/apiError'
import { LoginRequest } from '../../types/auth'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'

export function LoginForm() {
  const { logIn } = useAuth()
  const [serverError, setServerError] = useState('')
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginRequest>()

  async function onSubmit(data: LoginRequest) {
    setLoading(true)
    setServerError('')
    try {
      await logIn(data)
    } catch (error) {
      setServerError(getApiErrorMessage(error, 'Invalid email or password.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <Input
        label="Email"
        type="email"
        {...register('email', { required: 'Email is required' })}
        error={errors.email?.message}
      />
      <Input
        label="Password"
        type="password"
        {...register('password', { required: 'Password is required' })}
        error={errors.password?.message}
      />
      {serverError && <p className="text-sm text-red-600">{serverError}</p>}
      <Button type="submit" loading={loading}>
        Sign In
      </Button>
    </form>
  )
}
