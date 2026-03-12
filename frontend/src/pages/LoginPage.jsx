import React, {useState} from 'react';
import {useAuth} from '../components/AuthContext/UseAuth';
import {Link, Navigate} from 'react-router-dom';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';
import {Label} from '@/components/ui/label';
import {Card, CardContent} from '@/components/ui/card';

const LoginPage = () => {
    const {user, login, loading} = useAuth();
    const [formData, setFormData] = useState({
        email: '',
        password: ''
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    if (user) {
        return <Navigate to="/" replace/>;
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        const result = await login(formData.email, formData.password);

        if (!result.success) {
            setError(result.message);
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

                {/* Login Card */}
                <Card className="w-full max-w-md bg-white/90 backdrop-blur-lg shadow-xl border border-gray-200">
                    <CardContent className="pt-8 pb-8 px-8">
                        <form onSubmit={handleSubmit} className="space-y-5">
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
                                {isLoading ? 'Signing in...' : 'Sign In'}
                            </Button>

                            <div className="flex items-center justify-between pt-2">
                                <Link to="/forgot-password"
                                      className="text-sm text-gray-600 hover:text-gray-800 underline">
                                    Forgot password?
                                </Link>
                                <Link to="/register">
                                    <Button type="button" variant="outline"
                                            className="text-sm border-gray-300 text-gray-700 hover:bg-gray-100 bg-white">
                                        <span className="mr-1">+</span> Register
                                    </Button>
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

export default LoginPage;