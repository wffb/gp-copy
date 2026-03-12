import React, {useEffect, useState} from 'react';
import {useAuth} from '../components/AuthContext/UseAuth';
import {Link, Navigate, useSearchParams} from 'react-router-dom';
import {Button} from '@/components/ui/button';
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card';
import {api} from '@/services/api';

const VerifyEmailPage = () => {
    const {user, loading} = useAuth();
    const [searchParams] = useSearchParams();
    const [verificationState, setVerificationState] = useState('verifying'); // 'verifying', 'success', 'error'
    const [error, setError] = useState('');

    const token = searchParams.get('token');

    useEffect(() => {
        if (token) {
            verifyEmail(token);
        } else {
            setVerificationState('error');
            setError('No verification token provided');
        }
    }, [token]);

    const verifyEmail = async (token) => {
        try {
            const response = await api.verifyEmail(token);

            if (response.status === 204) {
                setVerificationState('success');
            }
        } catch (error) {
            setVerificationState('error');
            setError(error.response?.data?.message || 'Email verification failed');
        }
    };

    if (user) {
        return <Navigate to="/" replace/>;
    }

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

                {/* Verification Card */}
                <Card className="w-full max-w-md bg-white/90 backdrop-blur-lg shadow-xl border border-gray-200">
                    <CardHeader className="text-center pb-6 pt-8">
                        {verificationState === 'verifying' && (
                            <>
                                <CardTitle className="text-2xl font-semibold text-gray-800">Verifying
                                    Email...</CardTitle>
                                <CardDescription className="text-gray-600 text-base mt-4">
                                    Please wait while we verify your email address.
                                </CardDescription>
                            </>
                        )}

                        {verificationState === 'success' && (
                            <>
                                <CardTitle className="text-2xl font-semibold text-green-600">Email Verified!</CardTitle>
                                <CardDescription className="text-gray-600 text-base mt-4">
                                    Your email has been successfully verified. You can now sign in to your account.
                                </CardDescription>
                            </>
                        )}

                        {verificationState === 'error' && (
                            <>
                                <CardTitle className="text-2xl font-semibold text-red-600">Verification
                                    Failed</CardTitle>
                                <CardDescription className="text-gray-600 text-base mt-4">
                                    {error}
                                </CardDescription>
                            </>
                        )}
                    </CardHeader>

                    <CardContent className="text-center pb-8 px-8">
                        {verificationState === 'verifying' && (
                            <div className="flex justify-center">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                            </div>
                        )}

                        {verificationState === 'success' && (
                            <Link to="/login">
                                <Button className="w-full h-11 text-base bg-blue-600 hover:bg-blue-700 text-white">
                                    Sign In Now
                                </Button>
                            </Link>
                        )}

                        {verificationState === 'error' && (
                            <div className="flex flex-col space-y-3">
                                <Link to="/register">
                                    <Button variant="outline"
                                            className="w-full h-11 text-base border-gray-300 text-gray-700 hover:bg-gray-100 bg-white">
                                        Try Registration Again
                                    </Button>
                                </Link>
                                <Link to="/login">
                                    <Button className="w-full h-11 text-base bg-blue-600 hover:bg-blue-700 text-white">
                                        Back to Login
                                    </Button>
                                </Link>
                            </div>
                        )}
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

export default VerifyEmailPage;