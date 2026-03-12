import React, {useCallback, useEffect, useState} from 'react';
import {useNavigate} from 'react-router-dom';
import Header from '../components/Header/Header';
import FeedItem from '../components/Feed/FeedItem';
import {api} from '../services/api';
import {Button} from '@/components/ui/button';
import {ArrowLeft} from 'lucide-react';

const SavedArticlesPage = () => {
    const navigate = useNavigate();

    const [articles, setArticles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadBookmarks = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            const response = await api.getBookmarks();

            if (response.data?.code === 200) {
                setArticles(response.data.data || []);
            } else {
                setError(response.data?.message || "Failed to load saved articles");
            }
        } catch (err) {
            console.error("Error loading saved articles:", err);
            setError(err.response?.data?.message || "Failed to load saved articles");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadBookmarks();
    }, [loadBookmarks]);

    const handleBookmarkChange = (articleId, isBookmarked) => {
        if (!isBookmarked) {
            setArticles(prev => prev.filter(article => article.id !== articleId));
        }
    };

    const handleBackToFeed = () => {
        navigate('/');
    };

    if (loading && articles.length === 0) {
        return (
            <div
                className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col items-center justify-center transition-colors">
                <div
                    className="h-10 w-10 border-4 border-gray-300 dark:border-gray-600 border-t-blue-500 dark:border-t-blue-400 rounded-full animate-spin mb-4"></div>
                <p className="text-gray-600 dark:text-gray-300">Loading saved articles...</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
            <Header/>

            {/* Back to Articles Button */}
            <div className="max-w-7xl mx-auto px-5 pt-8">
                <Button
                    variant="outline"
                    onClick={() => navigate('/')}
                    className="flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white border-gray-300 dark:border-gray-600 dark:bg-gray-800"
                >
                    <ArrowLeft className="h-4 w-4"/>
                    Back to Articles
                </Button>
            </div>

            {/* Main content */}
            <main className="max-w-7xl mx-auto px-5 py-8">
                {error ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                        <p className="mb-4 text-red-600 dark:text-red-400">Failed to load: {error}</p>
                        <Button onClick={() => loadBookmarks()}>Retry</Button>
                    </div>
                ) : articles.length === 0 && !loading ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                        <div className="text-gray-400 dark:text-gray-500 mb-4">
                            <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor"
                                 viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                                      d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
                            </svg>
                        </div>
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Saved Articles</h3>
                        <p className="text-gray-500 dark:text-gray-400 mb-6">You haven't saved any articles yet. Start
                            bookmarking articles
                            you want to read later!</p>
                        <Button onClick={handleBackToFeed}>
                            Browse Articles
                        </Button>
                    </div>
                ) : (
                    <div className="space-y-6">
                        <div className="flex items-center justify-between">
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                                Your Saved Articles ({articles.length})
                            </h2>
                        </div>

                        {/* Articles grid */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                            {articles.map((article) => (
                                <FeedItem
                                    key={article.id}
                                    article={article}
                                    initialBookmarked={true}
                                    onBookmarkChange={handleBookmarkChange}
                                />
                            ))}
                        </div>

                        {/* Show total count */}
                        {articles.length > 0 && (
                            <div className="mt-6 flex justify-center">
                                <p className="text-center text-gray-500 dark:text-gray-400 text-sm">
                                    Showing all {articles.length} saved articles
                                </p>
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
};

export default SavedArticlesPage;
