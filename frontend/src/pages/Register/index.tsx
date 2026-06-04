import { Link } from 'react-router-dom'

import { RegisterForm } from '../../components/auth/RegisterForm'

export default function Register() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md rounded-lg border border-gray-200 bg-white p-6 shadow-sm sm:p-8">
        <h2 className="text-2xl font-bold mb-6 text-gray-900">Create Account</h2>
        <RegisterForm />
        <p className="mt-4 text-sm text-gray-600">
          Already have an account?{' '}
          <Link to="/login" className="text-indigo-600 hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </main>
  )
}
