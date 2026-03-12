import React from 'react';
import Feed from '../components/Feed/Feed';
import CategoryBar from '../components/Feed/CategoryBar';
import Header from '../components/Header/Header';
import {Navigate, useParams} from 'react-router-dom';
import {useAuth} from '../components/AuthContext/UseAuth';


const CATEGORIES = [
    "Physics", "Mathematics", "Computer", "Quantitative Biology",
    "Quantitative Finance", "Statistics", "Engineering", "Economics"
];


const deslug = (slug) => (slug ? slug.replace(/-/g, " ") : null);

const UserPortal = () => {
    const {category: categorySlug} = useParams(); // 可能是 undefined
    const currentCategory = categorySlug ? deslug(categorySlug) : null;
    const {user, loading} = useAuth();

    if (loading) {
        return (
            <div className="min-h-screen bg-white dark:bg-gray-900 flex items-center justify-center">
                <div className="text-gray-900 dark:text-white">Loading...</div>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace/>;
    }


    return (
        <div className="min-h-screen bg-white dark:bg-gray-900 transition-colors">
            <Header/>

            {/* Main content */}
            <main className="max-w-7xl mx-auto px-6 py-8">
                <CategoryBar categories={CATEGORIES} current={currentCategory}/>
                <Feed category={currentCategory}/>
            </main>

            {/* Footer */}
            <footer
                className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 mt-16 transition-colors">
                <div className="max-w-7xl mx-auto px-6 py-8">
                    <div className="text-center text-sm text-gray-500 dark:text-gray-400">
                        © 2025 NewsAI, All Rights Reserved.
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default UserPortal;
