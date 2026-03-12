import React, {useCallback, useEffect, useMemo, useState} from "react";
import {api} from "../../services/api";
import FeedItem from "./FeedItem";
import {Button} from "@/components/ui/button";

const Feed = ({category = null}) => {
    const [articles, setArticles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);

    const loadArticles = useCallback(async (pageNum = 1, reset = false) => {
        try {
            if (pageNum === 1) {
                setLoading(true);
                setError(null);
            } else {
                setLoadingMore(true);
            }

            const response = await api.getFeed(pageNum, 10);

            if (response.status === 200) {
                const newArticles = response.data.data.items || [];
                if (reset) setArticles(newArticles);
                else setArticles((prev) => [...prev, ...newArticles]);
                setHasMore(response.data.data.has_next || false);
                setPage(pageNum);
            } else {
                setError(response.data?.message || "Failed to load articles");
            }
        } catch (err) {
            console.error("Error loading articles:", err);
            setError(err.response?.data?.message || "Failed to load articles");
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    }, []);

    useEffect(() => {
        loadArticles(1, true);
    }, [loadArticles]);

    const loadMore = useCallback(() => {
        if (!loadingMore && hasMore) loadArticles(page + 1, false);
    }, [loadArticles, loadingMore, hasMore, page]);

    useEffect(() => {
        const handleScroll = () => {
            if (
                window.innerHeight + document.documentElement.scrollTop >=
                document.documentElement.offsetHeight - 1000
            ) {
                loadMore();
            }
        };
        window.addEventListener("scroll", handleScroll);
        return () => window.removeEventListener("scroll", handleScroll);
    }, [loadMore]);

    const visibleArticles = useMemo(() => {
        if (!category) return articles;
        return articles.filter(
            (a) =>
                Array.isArray(a.keywords) &&
                a.keywords.some((c) => c.toLowerCase() === category.toLowerCase())
        );
    }, [articles, category]);

    if (loading && articles.length === 0)
        return (
            <div className="flex flex-col items-center justify-center min-h-screen text-gray-600 dark:text-gray-300">
                <div
                    className="h-10 w-10 border-4 border-gray-300 dark:border-gray-600 border-t-blue-500 dark:border-t-blue-400 rounded-full animate-spin mb-4"></div>
                <p>Loading news...</p>
            </div>
        );

    if (error)
        return (
            <div className="flex flex-col items-center justify-center min-h-screen text-center">
                <p className="mb-4 text-red-600 dark:text-red-400">Failed to load: {error}</p>
                <Button onClick={() => loadArticles(1, true)}>Retry</Button>
            </div>
        );

    return (
        <div className="w-full">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {visibleArticles.map((article) => (
                    <FeedItem key={article.id} article={article}/>
                ))}
            </div>

            <div className="mt-12 flex flex-col items-center text-gray-600 dark:text-gray-300">
                {loadingMore && (
                    <>
                        <div
                            className="h-6 w-6 border-2 border-gray-300 dark:border-gray-600 border-t-blue-500 dark:border-t-blue-400 rounded-full animate-spin mb-2"></div>
                        <p className="text-sm">Loading more...</p>
                    </>
                )}
                {!hasMore && articles.length > 0 && !loadingMore && (
                    <p className="text-center text-gray-500 dark:text-gray-400 text-sm">No more content</p>
                )}
            </div>
        </div>
    );
};

export default Feed;
