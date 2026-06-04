import { Link } from 'react-router-dom'

import { LoginForm } from '../../components/auth/LoginForm'

export default function Login() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md rounded-lg border border-gray-200 bg-white p-6 shadow-sm sm:p-8">
        <h2 className="text-2xl font-bold mb-6 text-gray-900">Sign In</h2>
        <LoginForm />
        <p className="mt-4 text-sm text-gray-600">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="text-indigo-600 hover:underline">
            Register
          </Link>
        </p>
      </div>
    </main>
  )
}
