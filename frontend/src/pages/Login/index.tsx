import { Link } from 'react-router-dom'

import { LoginForm } from '../../components/auth/LoginForm'

export default function Login() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-surface p-4">
      <div className="w-full max-w-md rounded-lg border border-ink/10 bg-graphite-800 p-6 shadow-sm sm:p-8">
        <h2 className="text-2xl font-bold mb-6 text-ink">Sign In</h2>
        <LoginForm />
        <p className="mt-4 text-sm text-muted">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="font-medium text-ink hover:underline">
            Register
          </Link>
        </p>
      </div>
    </main>
  )
}
