import React, {useState} from 'react';
import {useNavigate} from 'react-router-dom';
import Header from '../components/Header/Header';
import {submitFeedback} from '../services/api';
import {Button} from '@/components/ui/button';
import {ArrowLeft} from 'lucide-react';

const ContactUsPage = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        email: '',
        message: ''
    });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitStatus, setSubmitStatus] = useState(null);

    const handleChange = (e) => {
        const {name, value} = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setSubmitStatus(null);

        try {
            await submitFeedback(formData);
            setSubmitStatus({type: 'success', message: 'Thank you for your feedback! We\'ll get back to you soon.'});
            // Reset form
            setFormData({
                first_name: '',
                last_name: '',
                email: '',
                message: ''
            });
        } catch (error) {
            setSubmitStatus({
                type: 'error',
                message: error.message || 'Failed to submit feedback. Please try again.'
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
            <Header/>

            {/* Back to Articles Button */}
            <div className="max-w-3xl mx-auto px-5 pt-8">
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
            <main className="max-w-3xl mx-auto px-5 py-8">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8 transition-colors">
                    <p className="text-gray-700 dark:text-gray-300 mb-6 text-left">
                        Reach out to us using the form below. We'd love to hear from you and explore new ways to make
                        science accessible to all!
                    </p>

                    <form onSubmit={handleSubmit}>
                        {/* Name Field */}
                        <div className="mb-6 text-left">
                            <label className="block text-gray-700 dark:text-gray-300 font-medium mb-2 text-left">
                                Name <span className="text-red-500">*</span>
                            </label>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <input
                                        type="text"
                                        name="first_name"
                                        value={formData.first_name}
                                        onChange={handleChange}
                                        required
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                    />
                                    <label className="block text-sm text-gray-500 dark:text-gray-400 mt-1">First</label>
                                </div>
                                <div>
                                    <input
                                        type="text"
                                        name="last_name"
                                        value={formData.last_name}
                                        onChange={handleChange}
                                        required
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                    />
                                    <label className="block text-sm text-gray-500 dark:text-gray-400 mt-1">Last</label>
                                </div>
                            </div>
                        </div>

                        {/* Email Field */}
                        <div className="mb-6 text-left">
                            <label className="block text-gray-700 dark:text-gray-300 font-medium mb-2 text-left">
                                Email <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                required
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            />
                        </div>

                        {/* Message Field */}
                        <div className="mb-6 text-left">
                            <label className="block text-gray-700 dark:text-gray-300 font-medium mb-2 text-left">
                                Message
                            </label>
                            <textarea
                                name="message"
                                value={formData.message}
                                onChange={handleChange}
                                rows="6"
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 resize-none bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            />
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="px-6 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                        >
                            {isSubmitting ? 'Submitting...' : 'Submit'}
                        </button>

                        {/* Status Message */}
                        {submitStatus && (
                            <div className={`mt-4 p-4 rounded ${
                                submitStatus.type === 'success'
                                    ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                                    : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                            }`}>
                                {submitStatus.message}
                            </div>
                        )}
                    </form>
                </div>
            </main>
        </div>
    );
};

export default ContactUsPage;
