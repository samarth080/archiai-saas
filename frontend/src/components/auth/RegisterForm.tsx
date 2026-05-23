import { useState } from 'react'
import { useForm } from 'react-hook-form'

import { useAuth } from '../../hooks/useAuth'
import { RegisterRequest } from '../../types/auth'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'

export function RegisterForm() {
  const { register: registerUser } = useAuth()
  const [serverError, setServerError] = useState('')
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterRequest>()

  async function onSubmit(data: RegisterRequest) {
    setLoading(true)
    setServerError('')
    try {
      await registerUser(data)
    } catch {
      setServerError('Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <Input
        label="Name"
        {...register('name', { required: 'Name is required' })}
        error={errors.name?.message}
      />
      <Input
        label="Email"
        type="email"
        {...register('email', { required: 'Email is required' })}
        error={errors.email?.message}
      />
      <Input
        label="Password"
        type="password"
        {...register('password', {
          required: 'Password is required',
          minLength: { value: 8, message: 'Password must be at least 8 characters' },
        })}
        error={errors.password?.message}
      />
      {serverError && <p className="text-sm text-red-600">{serverError}</p>}
      <Button type="submit" loading={loading}>
        Create Account
      </Button>
    </form>
  )
}
