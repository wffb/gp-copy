import React from 'react';
import FeedItem from '../Feed/FeedItem';

const SearchResults = ({
                           articles = [],
                           loading = false,
                           error = null,
                           query = '',
                           resultCount = 0,
                           onRetry
                       }) => {
    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-12">
                <div
                    className="h-10 w-10 border-4 border-gray-300 dark:border-gray-600 border-t-blue-500 dark:border-t-blue-400 rounded-full animate-spin mb-4"></div>
                <p className="text-gray-600 dark:text-gray-300">Searching for "{query}"...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center py-12 text-center">
                <p className="mb-4 text-red-600 dark:text-red-400">Search failed: {error}</p>
                <button
                    onClick={onRetry}
                    className="px-4 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600"
                >
                    Try Again
                </button>
            </div>
        );
    }

    // Empty state when no query has been made yet
    if (!query) {
        return (
            <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="text-gray-400 dark:text-gray-500 mb-4">
                    <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Search for News Articles</h3>
                <p className="text-gray-500 dark:text-gray-400">Enter keywords to find relevant articles quickly</p>
            </div>
        );
    }

    // Empty results state
    if (articles.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="text-gray-400 dark:text-gray-500 mb-4">
                    <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Results Found</h3>
                <p className="text-gray-500 dark:text-gray-400">No articles found for "{query}". Try different
                    keywords.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Results header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Search Results</h2>
                    <p className="text-gray-600 dark:text-gray-300 mt-1">
                        Found {resultCount} {resultCount === 1 ? 'article' : 'articles'} for "{query}"
                    </p>
                </div>
            </div>

            {/* Results grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {articles.map((article) => (
                    <FeedItem key={article.id} article={article}/>
                ))}
            </div>
        </div>
    );
};

export default SearchResults;