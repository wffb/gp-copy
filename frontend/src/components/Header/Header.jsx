import React from 'react';
import {useAuth} from '../AuthContext/UseAuth';
import {useNavigate} from 'react-router-dom';
import {Moon, Search, Sun} from "lucide-react";
import {useTheme} from '@/components/ThemeContext/ThemeContext';

const Header = () => {
    const {isAuthenticated, user, logout} = useAuth();
    const {isDark, toggleTheme} = useTheme();
    const navigate = useNavigate();

    const handleSearchClick = () => {
        navigate('/search');
    };

    const handleSavedArticlesClick = () => {
        navigate('/saved');
    };

    const handleInterestsClick = () => {
        navigate('/settings/interests');
    };

    const handleContactUsClick = () => {
        navigate('/contact');
    };

    const handleAboutClick = () => {
        navigate('/about');
    };

    const handleHomeClick = () => {
        navigate('/');
    };

    return (
        <header
            className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50 transition-colors">
            <div className="max-w-7xl mx-auto px-6 py-4">
                <div className="flex justify-between items-center">
                    <div className="flex items-center">
                        <button onClick={handleHomeClick}>
                            <h1 className="text-2xl font-bold text-blue-600 dark:text-blue-400 cursor-pointer hover:text-blue-700 dark:hover:text-blue-300 transition-colors">NewsAI</h1>
                        </button>
                    </div>
                    <div className="flex items-center gap-8">
                        <button
                            onClick={handleAboutClick}
                            className="text-sm text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white transition-colors uppercase tracking-wide"
                        >
                            ABOUT
                        </button>
                        <button
                            onClick={handleContactUsClick}
                            className="text-sm text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white transition-colors uppercase tracking-wide"
                        >
                            CONTACT
                        </button>
                        <button
                            onClick={handleSavedArticlesClick}
                            className="text-sm text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white transition-colors uppercase tracking-wide"
                        >
                            SAVED
                        </button>
                        <button
                            onClick={handleInterestsClick}
                            className="text-sm text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white transition-colors uppercase tracking-wide"
                        >
                            INTERESTS
                        </button>
                        <button
                            onClick={toggleTheme}
                            className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                            aria-label="Toggle theme"
                        >
                            {isDark ? (
                                <Sun className="h-4 w-4 text-yellow-500"/>
                            ) : (
                                <Moon className="h-4 w-4 text-gray-700"/>
                            )}
                        </button>
                        <div
                            className="w-8 h-8 bg-gray-800 dark:bg-gray-600 rounded-full flex items-center justify-center cursor-pointer hover:bg-gray-700 dark:hover:bg-gray-500 transition-colors">
                            <Search className="h-4 w-4 text-white" onClick={handleSearchClick}/>
                        </div>
                        {isAuthenticated && user && (
                            <button
                                onClick={logout}
                                className="text-sm text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white transition-colors uppercase tracking-wide"
                            >
                                LOGOUT
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;