import React, {useEffect, useState} from 'react';
import {useNavigate, useSearchParams} from 'react-router-dom';
import SearchInput from '../components/Search/SearchInput';
import SearchResults from '../components/Search/SearchResults';
import Header from '../components/Header/Header';
import {api} from '../services/api';
import {Button} from '@/components/ui/button';
import {ArrowLeft} from 'lucide-react';

const SearchPage = () => {
    const [searchParams, setSearchParams] = useSearchParams();
    const navigate = useNavigate();

    const [articles, setArticles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [resultCount, setResultCount] = useState(0);

    const query = searchParams.get('q') || '';

    const performSearch = async (searchQuery) => {
        if (!searchQuery.trim()) return;

        setLoading(true);
        setError(null);

        try {
            const response = await api.searchArticles(searchQuery);

            if (response.data?.code === 200) {
                const searchData = response.data.data;
                setArticles(searchData.items || []);
                setResultCount(searchData.total || 0);

                // Update URL with search query
                setSearchParams({q: searchQuery});
            } else {
                setError(response.data?.message || 'Search failed');
            }
        } catch (err) {
            console.error('Search error:', err);
            setError(err.response?.data?.message || 'Search failed');
        } finally {
            setLoading(false);
        }
    };

    // Perform search when component mounts with existing query
    useEffect(() => {
        if (query) {
            performSearch(query);
        }
    }, []);

    const handleRetry = () => {
        if (query) {
            performSearch(query);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
            {/* Header */}
            <Header/>

            {/* Back to Articles Button */}
            <div className="max-w-7xl mx-auto px-6 pt-8">
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
                {/* Search Input */}
                <div className="mb-8">
                    <SearchInput
                        onSearch={performSearch}
                        loading={loading}
                        initialQuery={query}
                    />
                </div>

                {/* Search Results */}
                <SearchResults
                    articles={articles}
                    loading={loading}
                    error={error}
                    query={query}
                    resultCount={resultCount}
                    onRetry={handleRetry}
                />
            </main>
        </div>
    );
};

export default SearchPage;