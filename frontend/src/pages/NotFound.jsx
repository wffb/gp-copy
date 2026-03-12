import React from 'react';
import {useNavigate} from 'react-router-dom';
import Header from '@/components/Header/Header';
import {Button} from '@/components/ui/button';
import {Home} from 'lucide-react';

const NotFound = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
            <Header/>

            {/* Main Content */}
            <main className="max-w-4xl mx-auto px-6 py-16">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-12 text-center transition-colors">
                    <div className="mb-8">
                        <h1 className="text-6xl font-bold text-gray-800 dark:text-white mb-4">404</h1>
                        <h2 className="text-2xl font-semibold text-gray-700 dark:text-gray-200 mb-2">Page Not Found</h2>
                        <p className="text-gray-600 dark:text-gray-400">
                            The page you're looking for doesn't exist or has been moved.
                        </p>
                    </div>

                    <Button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-2 mx-auto bg-blue-600 dark:bg-blue-500 hover:bg-blue-700 dark:hover:bg-blue-600 text-white"
                    >
                        <Home className="h-4 w-4"/>
                        Back to Home
                    </Button>
                </div>
            </main>
        </div>
    );
};

export default NotFound;