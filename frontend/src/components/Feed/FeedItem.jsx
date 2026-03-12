import React, {useState} from "react";
import {Link} from "react-router-dom";
import {Bookmark, BookmarkCheck} from "lucide-react";
import {api} from "../../services/api";

const FeedItem = ({article, initialBookmarked = false, onBookmarkChange}) => {
    const [isBookmarked, setIsBookmarked] = useState(initialBookmarked || article.is_bookmarked || false);
    const [bookmarkLoading, setBookmarkLoading] = useState(false);

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
        if (diffInHours < 1) return "Just now";
        if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? "s" : ""} ago`;
        const diffInDays = Math.floor(diffInHours / 24);
        return `${diffInDays} day${diffInDays > 1 ? "s" : ""} ago`;
    };

    const truncateText = (text, maxLength = 200) => {
        if (!text) return "";
        return text.length <= maxLength ? text : text.substring(0, maxLength) + "...";
    };

    const handleBookmarkToggle = async (e) => {
        e.preventDefault();
        e.stopPropagation();
        setBookmarkLoading(true);

        try {
            if (isBookmarked) {
                await api.unbookmarkArticle(article.id);
                setIsBookmarked(false);
                onBookmarkChange?.(article.id, false);
            } else {
                await api.bookmarkArticle(article.id);
                setIsBookmarked(true);
                onBookmarkChange?.(article.id, true);
            }
        } catch (error) {
            console.error('Failed to toggle bookmark:', error);
        } finally {
            setBookmarkLoading(false);
        }
    };

    return (
        <article className="group cursor-pointer">
            <Link to={`/article/${article.slug}`}
                  className="block bg-white dark:bg-gray-800 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-all">
                {/* Image with play button overlay */}
                <div
                    className="relative w-full h-48 overflow-hidden bg-gray-100 dark:bg-gray-700 transition-colors">
                    {article.featured_image_url ? (
                        <img
                            src={article.featured_image_url}
                            alt={article.title}
                            loading="lazy"
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                    ) : (
                        <div className="w-full h-full bg-gradient-to-br from-blue-500 to-purple-600"></div>
                    )}

                    {/* Bookmark Button */}
                    <button
                        onClick={handleBookmarkToggle}
                        disabled={bookmarkLoading}
                        className="absolute top-3 right-3 z-10 p-2 bg-white/80 dark:bg-gray-800/80 hover:bg-white dark:hover:bg-gray-700 rounded-full shadow-sm transition-colors disabled:opacity-50"
                        title={isBookmarked ? "Remove bookmark" : "Add bookmark"}
                    >
                        {bookmarkLoading ? (
                            <div
                                className="h-4 w-4 border-2 border-gray-300 dark:border-gray-500 border-t-blue-500 dark:border-t-blue-400 rounded-full animate-spin"/>
                        ) : isBookmarked ? (
                            <BookmarkCheck className="h-4 w-4 text-blue-600 dark:text-blue-400"/>
                        ) : (
                            <Bookmark
                                className="h-4 w-4 text-gray-400 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400"/>
                        )}
                    </button>
                </div>

                {/* Content */}
                <div className="p-4 space-y-2">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-2">
                        {article.title}
                    </h3>

                    <div className="text-sm text-gray-500 dark:text-gray-400">
                        {formatDate(article.created_at)}
                    </div>

                    <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed line-clamp-3">
                        {truncateText(article.description, 200)}
                    </p>

                    <div className="pt-2">
                        <span className="text-sm text-blue-600 dark:text-blue-400 font-medium group-hover:underline">
                            [Read more]
                        </span>
                    </div>
                </div>
            </Link>
        </article>
    );
};

export default FeedItem;
