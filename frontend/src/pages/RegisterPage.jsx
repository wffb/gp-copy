import React, {useState} from 'react';
import {useAuth} from '../components/AuthContext/UseAuth';
import {Link, Navigate} from 'react-router-dom';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';
import {Label} from '@/components/ui/label';
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card';
import {api} from '@/services/api';

const RegisterPage = () => {
    const {user, loading} = useAuth();
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        displayName: '',
        firstName: '',
        lastName: ''
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    if (user) {
        return <Navigate to="/" replace/>;
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        // Validate passwords match
        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match');
            setIsLoading(false);
            return;
        }

        try {
            const response = await api.register({
                email: formData.email,
                password: formData.password,
                display_name: formData.displayName,
                first_name: formData.firstName,
                last_name: formData.lastName
            });

            if (response.status === 204) {
                setSuccess(true);
            }
        } catch (error) {
            setError(error.response?.data?.message || 'Registration failed');
        }

        setIsLoading(false);
    };

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    if (loading) {
        return (
            <div
                className="min-h-screen relative overflow-hidden bg-cover bg-center bg-no-repeat flex items-center justify-center"
                style={{
                    backgroundImage: "url('/images/auth-background.png')"
                }}
            >
                <div className="text-lg text-gray-800">Loading...</div>
            </div>
        );
    }


    if (success) {
        return (
            <div
                className="min-h-screen relative overflow-hidden bg-cover bg-center bg-no-repeat"
                style={{
                    backgroundImage: "url('/images/auth-background.png')"
                }}
            >
                {/* Main content */}
                <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-8">
                    <div className="text-center mb-12">
                        <h1 className="text-4xl font-semibold text-gray-800">NewsAI</h1>
                    </div>

                    <Card className="w-full max-w-md bg-white/90 backdrop-blur-lg shadow-xl border border-gray-200">
                        <CardHeader className="text-center pb-6">
                            <CardTitle className="text-2xl font-semibold text-green-600">Registration
                                Successful!</CardTitle>
                            <CardDescription className="text-gray-600 text-base mt-4">
                                We've sent a verification email to <strong
                                className="text-gray-900">{formData.email}</strong>.
                                Please check your inbox and click the verification link to activate your account.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="text-center pb-8">
                            <Link to="/login">
                                <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                                    Back to Login
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>

                    <div className="mt-8 text-center">
                        <p className="text-sm text-gray-600">
                            © {new Date().getFullYear()} NewsAI, All Rights Reserved.
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div
            className="min-h-screen relative overflow-hidden bg-cover bg-center bg-no-repeat"
            style={{
                backgroundImage: "url('/images/auth-background.png')"
            }}
        >

            {/* Main content */}
            <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-8">
                {/* Title */}
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-semibold text-gray-800">NewsAI</h1>
                </div>

                {/* Register Card */}
                <Card className="w-full max-w-md bg-white/90 backdrop-blur-lg shadow-xl border border-gray-200">
                    <CardHeader className="text-center pb-6 pt-8">
                        <CardTitle className="text-2xl font-semibold text-gray-800">
                            Register For This Site
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="pb-8 px-8">
                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div className="space-y-2">
                                <Label htmlFor="displayName" className="text-sm font-normal text-gray-700">
                                    Display Name
                                </Label>
                                <Input
                                    id="displayName"
                                    name="displayName"
                                    type="text"
                                    value={formData.displayName}
                                    onChange={handleChange}
                                    placeholder="Value"
                                    className="h-11 bg-white border-gray-300 text-gray-900 placeholder:text-gray-500"
                                    required
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="firstName" className="text-sm font-normal text-gray-700">
                                        First Name
                                    </Label>
                                    <Input
                                        id="firstName"
                                        name="firstName"
                                        type="text"
                                        value={formData.firstName}
                                        onChange={handleChange}
                                        placeholder="Value"
                                        className="h-11 bg-white border-gray-300 text-gray-900 placeholder:text-gray-500"
                                        required
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="lastName" className="text-sm font-normal text-gray-700">
                                        Last Name
                                    </Label>
                                    <Input
                                        id="lastName"
                                        name="lastName"
                                        type="text"
                                        value={formData.lastName}
                                        onChange={handleChange}
                                        placeholder="Value"
                                        className="h-11 bg-white border-gray-300 text-gray-900 placeholder:text-gray-500"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="email" className="text-sm font-normal text-gray-700">
                                    Email
                                </Label>
                                <Input
                                    id="email"
                                    name="email"
                                    type="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    placeholder="Value"
                                    className="h-11 bg-white border-gray-300 text-gray-900 placeholder:text-gray-500"
                                    required
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="password" className="text-sm font-normal text-gray-700">
                                        Password
                                    </Label>
                                    <Input
                                        id="password"
                                        name="password"
                                        type="password"
                                        value={formData.password}
                                        onChange={handleChange}
                                        placeholder="Value"
                                        className="h-11 bg-white border-gray-300 text-gray-900 placeholder:text-gray-500"
                                        required
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="confirmPassword" className="text-sm font-normal text-gray-700">
                                        Confirm Password
                                    </Label>
                                    <Input
                                        id="confirmPassword"
                                        name="confirmPassword"
                                        type="password"
                                        value={formData.confirmPassword}
                                        onChange={handleChange}
                                        placeholder="Value"
                                        className="h-11 bg-white border-gray-300 text-gray-900 placeholder:text-gray-500"
                                        required
                                    />
                                </div>
                            </div>

                            {error && (
                                <div
                                    className="bg-red-500/20 border border-red-500/30 text-red-700 px-4 py-3 rounded-md text-sm">
                                    {error}
                                </div>
                            )}

                            <Button
                                type="submit"
                                className="w-full h-11 text-base bg-blue-600 hover:bg-blue-700 text-white"
                                disabled={isLoading}
                            >
                                {isLoading ? 'Creating Account...' : 'Register'}
                            </Button>

                            <div className="flex items-center justify-between pt-2">
                                <Link to="/login" className="text-sm text-gray-600 hover:text-gray-800 underline">
                                    Log in
                                </Link>
                                <Link to="/forgot-password"
                                      className="text-sm text-gray-600 hover:text-gray-800 underline">
                                    Lost your password?
                                </Link>
                            </div>
                        </form>
                    </CardContent>
                </Card>

                {/* Footer */}
                <div className="mt-8 text-center">
                    <p className="text-sm text-gray-600">
                        © {new Date().getFullYear()} NewsAI, All Rights Reserved.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default RegisterPage;