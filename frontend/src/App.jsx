import {BrowserRouter as Router, Route, Routes} from 'react-router-dom';
import {HelmetProvider} from 'react-helmet-async';
import './App.css'
import {AuthProvider} from "./components/AuthContext/AuthContext.jsx";
import {ThemeProvider} from "@/components/ThemeContext/ThemeContext.jsx";
import UserPortal from "./pages/UserPortal.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import VerifyEmailPage from "./pages/VerifyEmailPage.jsx";
import ArticleDetail from "./components/ArticleDetail/ArticleDetail.jsx";
import NotFound from "./pages/NotFound.jsx";
import ProtectedRoute from "@/ProtectedRoute/ProtectedRoute.jsx";
import InterestsSettings from '@/pages/InterestsSettings';
import SearchPage from "./pages/SearchPage.jsx";
import SavedArticlesPage from "./pages/SavedArticlesPage.jsx";
import ContactUsPage from "./pages/ContactUsPage.jsx";
import AboutPage from "./pages/AboutPage.jsx";

function App() {
    return (
        <HelmetProvider>
            <ThemeProvider>
                <AuthProvider>
                    <Router>
                        <Routes>
                            <Route path="/login" element={<LoginPage/>}/>
                            <Route path="/register" element={<RegisterPage/>}/>
                            <Route path="/verify" element={<VerifyEmailPage/>}/>
                            <Route path="/about" element={<AboutPage/>}/>
                            <Route path="/" element={<UserPortal/>}/>
                            <Route element={<ProtectedRoute/>}>
                                <Route path="/settings/interests" element={<InterestsSettings/>}/>
                                <Route path="/article/:articleId" element={<ArticleDetail/>}/>
                                <Route path="/search" element={<SearchPage/>}/>
                                <Route path="/saved" element={<SavedArticlesPage/>}/>
                                <Route path="/contact" element={<ContactUsPage/>}/>
                            </Route>
                            <Route path="/:category" element={<UserPortal/>}/>
                            <Route path="*" element={<NotFound/>}/>
                        </Routes>
                    </Router>
                </AuthProvider>
            </ThemeProvider>
        </HelmetProvider>
    )
}

export default App