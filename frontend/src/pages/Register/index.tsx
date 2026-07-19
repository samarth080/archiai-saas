import { Link } from 'react-router-dom'

import { RegisterForm } from '../../components/auth/RegisterForm'

export default function Register() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-surface p-4">
      <div className="w-full max-w-md rounded-lg border border-ink/10 bg-graphite-800 p-6 shadow-sm sm:p-8">
        <h2 className="text-2xl font-bold mb-6 text-ink">Create Account</h2>
        <RegisterForm />
        <p className="mt-4 text-sm text-muted">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-ink hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </main>
  )
}
