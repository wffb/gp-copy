import React from 'react';
import {useNavigate} from 'react-router-dom';
import Header from '../components/Header/Header';
import {Button} from '@/components/ui/button';
import {ArrowLeft} from 'lucide-react';

const AboutPage = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
            <Header/>

            {/* Back to Articles Button */}
            <div className="max-w-4xl mx-auto px-8 pt-8">
                <Button
                    variant="outline"
                    onClick={() => navigate('/')}
                    className="flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white border-gray-300 dark:border-gray-600 dark:bg-gray-800"
                >
                    <ArrowLeft className="h-4 w-4"/>
                    Back to Articles
                </Button>
            </div>

            {/* Main Content */}
            <main className="max-w-4xl mx-auto px-8 py-8">
                <div className="space-y-8 text-gray-700 dark:text-gray-300 text-lg leading-relaxed">
                    <p>
                        Every day, thousands of scientific papers are published, but only a small fraction reach the
                        public in a way that is clear and easy to understand.
                    </p>

                    <p>
                        The Science Archive develops AI technology to analyze and interpret the latest research from
                        arXiv, a pre-print repository used by the scientific community.
                    </p>

                    <p>
                        By analyzing the hundreds of scientific papers uploaded to arXiv daily, we transform complex
                        research into engaging and unbiased news articles that make cutting-edge science accessible, to
                        keep everyone updated on the latest discoveries.
                    </p>

                    <p>
                        To find out more about The Science Archive project, please contact us.
                    </p>
                </div>
            </main>
        </div>
    );
};

export default AboutPage;