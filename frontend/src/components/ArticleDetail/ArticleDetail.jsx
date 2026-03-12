import React, {useEffect, useState} from "react";
import {useNavigate, useParams} from "react-router-dom";
import {Helmet} from "react-helmet-async";
import Header from "../Header/Header";
import {api} from "../../services/api";
import {Button} from "@/components/ui/button";
import {Badge} from "@/components/ui/badge";
import {ArrowLeft, Bookmark, Calendar, Eye, Share2} from "lucide-react";

// Block component to render different block types
const Block = ({ block }) => {
    switch (block.block_type) {
        case "title":
            return <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4 mt-8 first:mt-0">{block.content}</h1>;
        case "subheading":
            return <h2 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-200 mb-3 mt-6">{block.content}</h2>;
        case "paragraph":
            return <p className="text-base md:text-lg text-gray-700 dark:text-gray-300 mb-4 leading-relaxed">{block.content}</p>;
        case "quote":
            return (
                <blockquote className="border-l-4 border-blue-500 dark:border-blue-400 pl-6 italic text-gray-700 dark:text-gray-300 my-6 text-lg">
                    {block.content}
                </blockquote>
            );
        case "image":
            return (
                <div className="my-8 rounded-xl overflow-hidden shadow-lg">
                    <img 
                        src={block.content} 
                        alt={block.caption || "Article image"} 
                        className="w-full h-auto object-cover"
                        onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'block';
                        }}
                    />
                    <div 
                        className="hidden bg-gray-100 dark:bg-gray-700 p-8 text-center text-gray-500 dark:text-gray-400"
                        style={{display: 'none'}}
                    >
                        <p>图片加载失败</p>
                        <p className="text-sm mt-2">URL: {block.content}</p>
                    </div>
                    {block.caption && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 px-4 italic text-center">
                            {block.caption}
                        </p>
                    )}
                </div>
            );
        case "list":
            return (
                <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 mb-4 space-y-2 ml-4">
                    {block.items?.map((item, idx) => (
                        <li key={idx} className="text-base md:text-lg">{item}</li>
                    ))}
                </ul>
            );
        case "code":
            return (
                <pre className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg overflow-x-auto my-4">
                    <code className="text-sm text-gray-800 dark:text-gray-200">{block.content}</code>
                </pre>
            );
        default:
            return null;
    }
};

const ArticleDetail = () => {
    const {articleId} = useParams();
    const navigate = useNavigate();
    const [article, setArticle] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadArticle = async () => {
            try {
                setLoading(true);
                setError(null);
                const response = await api.getArticle(articleId);
                if (response.status === 200) {
                    setArticle(response.data.data);
                } else {
                    setError(response.data?.message || "Failed to load article");
                }
            } catch (err) {
                console.error(err);
                setError(err.response?.data?.message || "Failed to load article");
            } finally {
                setLoading(false);
            }
        };
        if (articleId) loadArticle();
    }, [articleId]);

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString("zh-CN", {
            year: "numeric",
            month: "long",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    if (loading)
        return (
            <div
                className="flex flex-col items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-300 transition-colors">
                <div
                    className="h-10 w-10 border-4 border-gray-300 dark:border-gray-600 border-t-blue-500 dark:border-t-blue-400 rounded-full animate-spin mb-4"></div>
                <p>Loading article...</p>
            </div>
        );

    if (error)
        return (
            <div
                className="flex flex-col items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900 text-center transition-colors">
                <h2 className="text-xl font-bold text-red-600 dark:text-red-400 mb-2">Failed to Load</h2>
                <p className="mb-4 text-gray-700 dark:text-gray-300">{error}</p>
                <Button variant="outline" onClick={() => navigate(-1)}>
                    Back to Articles
                </Button>
            </div>
        );

    if (!article)
        return (
            <div
                className="flex flex-col items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900 text-center transition-colors">
                <h2 className="text-xl font-bold text-gray-700 dark:text-gray-200 mb-2">Article Not Found</h2>
                <p className="mb-4 text-gray-600 dark:text-gray-400">Sorry, the article you are looking for does not
                    exist or has been deleted.</p>
                <Button variant="outline" onClick={() => navigate(-1)}>
                    Back to Articles
                </Button>
            </div>
        );

    return (
        <div
            className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 transition-colors">
            <Helmet>
                <title>{article.title} - NewsAI</title>
                <meta name="description" content={article.description}/>
                <meta name="keywords" content={article.keywords?.join(", ")}/>
                <meta name="author" content={article.author || article.source}/>
            </Helmet>

            <Header/>

            {/* Back Button */}
            <div className="max-w-4xl mx-auto px-4 py-4">
                <Button
                    variant="ghost"
                    onClick={() => navigate(-1)}
                    className="flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
                >
                    <ArrowLeft className="h-4 w-4"/>
                    Back to Articles
                </Button>
            </div>

            {/* Main Content */}
            <article className="max-w-4xl mx-auto px-4 py-8">
                {/* Article Header */}
                <header className="mb-8">
                    <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4 leading-tight">
                        {article.title}
                    </h1>

                    {/* Meta Information */}
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-6">
                        <div className="flex items-center gap-1.5">
                            <Calendar className="h-4 w-4"/>
                            <span>{formatDate(article.created_at)}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <Eye className="h-4 w-4"/>
                            <span>{article.view_count || 0} views</span>
                        </div>
                    </div>

                    {/* Keywords */}
                    {article.keywords && article.keywords.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-6">
                            {article.keywords.map((keyword, index) => (
                                <Badge
                                    key={index}
                                    variant="secondary"
                                    className="bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/50"
                                >
                                    {keyword}
                                </Badge>
                            ))}
                        </div>
                    )}
                </header>

                {/* Featured Image */}
                {article.featured_image_url && (
                    <div className="mb-8 rounded-xl overflow-hidden shadow-lg">
                        <img
                            src={article.featured_image_url}
                            alt={article.title}
                            className="w-full h-auto object-cover"
                        />
                    </div>
                )}

                {/* Article Content */}
                <div
                    className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-8 md:p-12 transition-colors">
                    {/* Description */}
                    <div
                        className="text-xl text-gray-700 dark:text-gray-300 mb-8 leading-relaxed font-medium border-l-4 border-blue-500 dark:border-blue-400 pl-6 italic">
                        {article.description}
                    </div>

                    {/* Main Content */}
                    <div className="prose prose-lg dark:prose-invert max-w-none">
                        {Array.isArray(article.blocks) ? (
                            // Render blocks if blocks is an array (new format)
                            article.blocks
                                .sort((a, b) => (a.order_index || 0) - (b.order_index || 0))
                                .map((block) => (
                                    <Block key={block.id} block={block} />
                                ))
                        ) : Array.isArray(article.content) ? (
                            // Fallback: render content blocks (old format)
                            article.content.map((block, index) => (
                                <Block key={block.id || index} block={block} />
                            ))
                        ) : (
                            // Fallback: split by newlines for legacy string content
                            article.content?.split("\n").map((paragraph, index) => (
                                paragraph.trim() && (
                                    <p key={index} className="text-base md:text-lg text-gray-700 dark:text-gray-300 mb-4 leading-relaxed">
                                        {paragraph}
                                    </p>
                                )
                            ))
                        )}
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="mt-8 flex flex-wrap gap-3 justify-center md:justify-end">
                    <Button
                        variant="outline"
                        className="flex items-center gap-2 border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
                    >
                        <Share2 className="h-4 w-4"/>
                        Share
                    </Button>
                    <Button
                        className="flex items-center gap-2 bg-blue-600 dark:bg-blue-500 hover:bg-blue-700 dark:hover:bg-blue-600"
                    >
                        <Bookmark className="h-4 w-4"/>
                        Bookmark
                    </Button>
                </div>
            </article>
        </div>
    );
};

export default ArticleDetail;
