import { Link } from 'react-router-dom'

import { LoginForm } from '../../components/auth/LoginForm'

export default function Login() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-lg shadow w-full max-w-md">
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
