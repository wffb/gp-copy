import {http, HttpResponse} from "msw";
import {createErrorResponse, createSuccessResponse} from "./utils";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

// Mock user
const mockUser = {
    id: "6b7b2a55-8d8b-4a22-86d6-2b8b0c9a3c11",
    email: "test@example.com",
    display_name: "Test User",
    first_name: "Test",
    last_name: "User",
    role: [{id: "1", name: "USER"}],
    email_verified_at: "2024-09-18T12:34:56Z",
    profile_image_url: "https://cdn.example.com/u/123.png",
    created_at: "2024-09-18T12:34:56Z",
    updated_at: "2024-09-18T12:34:56Z",
};

// Mock fields/subtopics with proper structure matching API documentation
const FIELDS = [
    {
        id: "02f5a1b2-c3d4-4e5f-6a7b-8c9d0e1f2a3b",
        code: "PHY",
        name: "Physics",
        sort_order: 1,
        subfields: [
            {id: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d", code: "ASTRO", name: "Astrophysics", sort_order: 10},
            {id: "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e", code: "COND", name: "Condensed Matter", sort_order: 20},
            {id: "c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f", code: "HEP", name: "High Energy Physics", sort_order: 30},
            {id: "d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a", code: "QUANTUM", name: "Quantum Physics", sort_order: 40}
        ]
    },
    {
        id: "12a3b4c5-d6e7-4f8a-9b0c-1d2e3f4a5b6c",
        code: "MATH",
        name: "Mathematics",
        sort_order: 2,
        subfields: [
            {id: "e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b", code: "PROB", name: "Probability", sort_order: 10},
            {id: "f6a7b8c9-d0e1-4f2a-3b4c-5d6e7f8a9b0c", code: "STAT", name: "Statistics", sort_order: 20},
            {id: "a7b8c9d0-e1f2-4a3b-4c5d-6e7f8a9b0c1d", code: "OPT", name: "Optimization", sort_order: 30},
            {id: "b8c9d0e1-f2a3-4b4c-5d6e-7f8a9b0c1d2e", code: "ALG", name: "Algebra", sort_order: 40}
        ]
    },
    {
        id: "23b4c5d6-e7f8-4a9b-0c1d-2e3f4a5b6c7d",
        code: "CS",
        name: "Computer Science",
        sort_order: 3,
        subfields: [
            {id: "c9d0e1f2-a3b4-4c5d-6e7f-8a9b0c1d2e3f", code: "AI", name: "Artificial Intelligence", sort_order: 10},
            {id: "d0e1f2a3-b4c5-4d6e-7f8a-9b0c1d2e3f4a", code: "DB", name: "Databases", sort_order: 20},
            {id: "e1f2a3b4-c5d6-4e7f-8a9b-0c1d2e3f4a5b", code: "SYS", name: "Systems", sort_order: 30},
            {
                id: "f2a3b4c5-d6e7-4f8a-9b0c-1d2e3f4a5b6c",
                code: "HCI",
                name: "Human-Computer Interaction",
                sort_order: 40
            }
        ]
    },
    {
        id: "34c5d6e7-f8a9-4b0c-1d2e-3f4a5b6c7d8e",
        code: "QBIO",
        name: "Quantitative Biology",
        sort_order: 4,
        subfields: [
            {id: "a3b4c5d6-e7f8-4a9b-0c1d-2e3f4a5b6c7d", code: "GEN", name: "Genetics", sort_order: 10},
            {id: "b4c5d6e7-f8a9-4b0c-1d2e-3f4a5b6c7d8e", code: "EPI", name: "Epidemiology", sort_order: 20},
            {id: "c5d6e7f8-a9b0-4c1d-2e3f-4a5b6c7d8e9f", code: "NEURO", name: "Neuroscience", sort_order: 30},
            {id: "d6e7f8a9-b0c1-4d2e-3f4a-5b6c7d8e9f0a", code: "IMMUNO", name: "Immunology", sort_order: 40}
        ]
    },
    {
        id: "45d6e7f8-a9b0-4c1d-2e3f-4a5b6c7d8e9f",
        code: "QFIN",
        name: "Quantitative Finance",
        sort_order: 5,
        subfields: [
            {id: "e7f8a9b0-c1d2-4e3f-4a5b-6c7d8e9f0a1b", code: "PORT", name: "Portfolio Management", sort_order: 10},
            {id: "f8a9b0c1-d2e3-4f4a-5b6c-7d8e9f0a1b2c", code: "RISK", name: "Risk Management", sort_order: 20},
            {id: "a9b0c1d2-e3f4-4a5b-6c7d-8e9f0a1b2c3d", code: "COMPFIN", name: "Computational Finance", sort_order: 30}
        ]
    },
    {
        id: "56e7f8a9-b0c1-4d2e-3f4a-5b6c7d8e9f0a",
        code: "STATS",
        name: "Statistics",
        sort_order: 6,
        subfields: [
            {id: "b0c1d2e3-f4a5-4b6c-7d8e-9f0a1b2c3d4e", code: "ML", name: "Machine Learning", sort_order: 10},
            {id: "c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f", code: "METH", name: "Methodology", sort_order: 20},
            {id: "d2e3f4a5-b6c7-4d8e-9f0a-1b2c3d4e5f6a", code: "THEORY", name: "Theory", sort_order: 30}
        ]
    },
    {
        id: "67f8a9b0-c1d2-4e3f-4a5b-6c7d8e9f0a1b",
        code: "ENG",
        name: "Engineering",
        sort_order: 7,
        subfields: [
            {id: "e3f4a5b6-c7d8-4e9f-0a1b-2c3d4e5f6a7b", code: "EE", name: "Electrical Engineering", sort_order: 10},
            {id: "f4a5b6c7-d8e9-4f0a-1b2c-3d4e5f6a7b8c", code: "SYSCON", name: "Systems and Control", sort_order: 20}
        ]
    },
    {
        id: "78a9b0c1-d2e3-4f4a-5b6c-7d8e9f0a1b2c",
        code: "ECON",
        name: "Economics",
        sort_order: 8,
        subfields: [
            {id: "a5b6c7d8-e9f0-4a1b-2c3d-4e5f6a7b8c9d", code: "ECONM", name: "Econometrics", sort_order: 10},
            {id: "b6c7d8e9-f0a1-4b2c-3d4e-5f6a7b8c9d0e", code: "THEOR", name: "Theoretical Economics", sort_order: 20}
        ]
    }
];

// Mock user interests - store as Set of field IDs (UUIDs) for easier manipulation
let mockUserInterestIds = new Set([
    "23b4c5d6-e7f8-4a9b-0c1d-2e3f4a5b6c7d", // Computer Science
    "c9d0e1f2-a3b4-4c5d-6e7f-8a9b0c1d2e3f", // AI
    "12a3b4c5-d6e7-4f8a-9b0c-1d2e3f4a5b6c", // Mathematics
    "e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b"  // Probability
]);

// Mock login state - check localStorage for persistence across page refreshes
const getLoginState = () => {
    return localStorage.getItem('msw_logged_in') === 'true';
};

const setLoginState = (state) => {
    localStorage.setItem('msw_logged_in', state.toString());
};

// Initialize login state from localStorage
let isLoggedIn = getLoginState();

// Mock bookmarks storage with localStorage persistence
const getBookmarks = () => {
    const stored = localStorage.getItem('msw_bookmarks');
    return stored ? JSON.parse(stored) : [];
};

const setBookmarks = (bookmarks) => {
    localStorage.setItem('msw_bookmarks', JSON.stringify(bookmarks));
};

let mockBookmarks = getBookmarks();

export const handlers = [
    // login
    http.post(`${API_BASE_URL}/api/v1/login`, async ({request}) => {
        const credentials = await request.json();
        if (!credentials.email || !credentials.password)
            return HttpResponse.json(createErrorResponse("BadRequest", "Email and password are required", 400), {status: 400});
        if (credentials.email === "test@example.com" && credentials.password === "password123") {
            isLoggedIn = true;
            setLoginState(true);
            return new HttpResponse(null, {status: 204});
        }
        return HttpResponse.json(createErrorResponse("InvalidCredentialsError", "Invalid credentials", 401), {status: 401});
    }),

    // get current user
    http.get(`${API_BASE_URL}/api/v1/users/me`, () => {
        // Always check localStorage for the most up-to-date login state
        isLoggedIn = getLoginState();
        if (!isLoggedIn) {
            return HttpResponse.json(createErrorResponse("Unauthorized", "User not authenticated", 401), {status: 401});
        }
        return HttpResponse.json(createSuccessResponse(mockUser), {status: 200});
    }),

    // logout
    http.post(`${API_BASE_URL}/api/v1/logout`, () => {
        isLoggedIn = false;
        setLoginState(false);
        return new HttpResponse(null, {status: 204});
    }),

    // register
    http.post(`${API_BASE_URL}/api/v1/register`, async ({request}) => {
        const userData = await request.json();
        if (!userData.email || !userData.password)
            return HttpResponse.json(createErrorResponse("ValidationError", "Email and password are required", 422), {status: 422});
        return new HttpResponse(null, {status: 204});
    }),

    // verify email
    http.post(`${API_BASE_URL}/api/v1/verify-email`, async ({request}) => {
        const {token} = await request.json();
        if (!token)
            return HttpResponse.json(createErrorResponse("InvalidVerificationTokenError", "Invalid verification token", 400), {status: 400});
        return new HttpResponse(null, {status: 204});
    }),

    // resend email verification
    http.post(`${API_BASE_URL}/api/v1/resend-email-verification`, async ({request}) => {
        const {email, password} = await request.json();
        if (!email || !password)
            return HttpResponse.json(createErrorResponse("InvalidCredentialsError", "Email and password are required", 401), {status: 401});
        return new HttpResponse(null, {status: 204});
    }),

    // ------------------- Articles API -------------------

    // GET /articles/ with pagination
    http.get(`${API_BASE_URL}/api/v1/articles`, async ({request}) => {
        const url = new URL(request.url);
        const page = parseInt(url.searchParams.get("page")) || 1;
        const limit = parseInt(url.searchParams.get("limit")) || 10;
        const category = url.searchParams.get("category");

        // Mock articles by category
        const physicsArticles = [
            {
                title: "Quantum Computing Breakthrough: New Qubit Design Achieves 99.9% Fidelity",
                description: "Researchers have developed a revolutionary qubit design that maintains quantum coherence for unprecedented durations, marking a significant step toward practical quantum computing applications.",
                category: "Physics",
                keywords: ["quantum computing", "physics", "technology"]
            },
            {
                title: "Dark Matter Detection: Advanced Particle Detector Reveals New Insights",
                description: "Scientists using the latest generation of underground particle detectors have identified potential dark matter interactions, bringing us closer to understanding this mysterious component of the universe.",
                category: "Physics",
                keywords: ["dark matter", "particle physics", "cosmology"]
            },
            {
                title: "Room-Temperature Superconductivity: Revolutionary Material Discovery",
                description: "A team of physicists has synthesized a new material that exhibits superconducting properties at room temperature and ambient pressure, potentially revolutionizing energy transmission and storage.",
                category: "Physics",
                keywords: ["superconductivity", "materials science", "energy"]
            }
        ];

        const mathematicsArticles = [
            {
                title: "Prime Number Theorem: New Proof Simplifies Century-Old Mathematical Problem",
                description: "Mathematicians have discovered an elegant new proof for the prime number theorem, providing fresh insights into the distribution of prime numbers and opening new avenues for research.",
                category: "Mathematics",
                keywords: ["prime numbers", "number theory", "mathematics"]
            },
            {
                title: "Topology Breakthrough: Novel Approach to Understanding High-Dimensional Spaces",
                description: "A groundbreaking mathematical framework has been developed to analyze complex topological structures in higher dimensions, with applications in physics and computer science.",
                category: "Mathematics",
                keywords: ["topology", "geometry", "mathematical theory"]
            },
            {
                title: "Machine Learning Mathematics: New Optimization Algorithms Enhance AI Performance",
                description: "Researchers have developed innovative mathematical optimization techniques that significantly improve the efficiency and accuracy of machine learning algorithms across various applications.",
                category: "Mathematics",
                keywords: ["optimization", "machine learning", "algorithms"]
            }
        ];

        const otherArticles = [
            {
                title: "Breaking the Cycle: A Novel Approach to Reducing Reincarceration Rates",
                description: "A novel approach to breaking the cycle of incarceration has been developed by researchers in partnership with a county government in the United States. The project aims to reduce reincarceration rates among individuals with complex needs, such as mental illness, substance dependence, and homelessness.",
                category: "Social Science",
                keywords: ["news", "update", "social science"]
            }
        ];

        let availableArticles = [...physicsArticles, ...mathematicsArticles, ...otherArticles];

        // Filter by category if specified
        if (category && category.toLowerCase() !== 'all') {
            availableArticles = availableArticles.filter(article =>
                article.category.toLowerCase() === category.toLowerCase()
            );
        }

        // Generate articles for pagination
        const TOTAL_ARTICLES = availableArticles.length > 0 ? Math.max(100, availableArticles.length) : 100;

        const items = Array.from({length: Math.min(limit, availableArticles.length)}, (_, i) => {
            const articleIndex = ((page - 1) * limit + i) % availableArticles.length;
            const template = availableArticles[articleIndex];
            const idx = (page - 1) * limit + i + 1;

            return {
                id: `article-${idx}`,
                title: template.title,
                description: template.description,
                category: template.category,
                keywords: template.keywords,
                slug: `article-title-${idx}`,
                featured_image_url: `https://picsum.photos/800/400?random=${idx}`,
                view_count: Math.floor(Math.random() * 1000),
                created_at: new Date(Date.now() - idx * 3600 * 1000).toISOString(),
                updated_at: new Date(Date.now() - idx * 1800 * 1000).toISOString(),
            };
        });

        return HttpResponse.json(
            createSuccessResponse({
                items,
                total: TOTAL_ARTICLES,
                page,
                limit,
                total_pages: Math.ceil(TOTAL_ARTICLES / limit),
                has_next: page < Math.ceil(TOTAL_ARTICLES / limit),
                has_prev: page > 1,
            }),
            {status: 200}
        );
    }),

    // GET /article/:articleId detail (note: singular 'article')
    http.get(`${API_BASE_URL}/api/v1/articles/:articleId`, async ({params}) => {
        const {articleId} = params;
        const mockArticle = {
            id: articleId,
            title: `Breaking the Cycle: A Novel Approach to Reducing Reincarceration Rates`,
            description: `This is a detailed description for ${articleId}: A novel approach to breaking the cycle of incarceration has been developed by researchers in partnership with a county government in the United States. The project aims to reduce reincarceration rates among individuals with complex needs, such as mental illness`,
            keywords: ["news", "update", `topic-${articleId}`],
            slug: `detailed-article-${articleId}`,
            featured_image_url: `https://picsum.photos/1200/600?random=${articleId}`,
            view_count: Math.floor(Math.random() * 5000),
            created_at: new Date(Date.now() - 5 * 3600 * 1000).toISOString(),
            updated_at: new Date().toISOString(),
            is_bookmarked: false,
            // Blocks array matching backend format
            blocks: [
                {
                    id: "42666b68-6eed-44db-89f0-9cf0aedaf1ea",
                    block_type: "title",
                    content: "Breaking the Cycle: A Novel Approach to Reducing Reincarceration Rates",
                    order_index: 0,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: "1b6a990b-4e58-4246-83a5-28d7fa29acf0",
                    block_type: "paragraph",
                    content: "A novel approach to breaking the cycle of incarceration has been developed by researchers in partnership with a county government in the United States. The project aims to reduce reincarceration rates among individuals with complex needs, such as mental illness, substance dependence, and homelessness.",
                    order_index: 1,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: "c2b83f3b-ec72-4bfe-b5e4-93220229d42e",
                    block_type: "subheading",
                    content: "The Problem: A Pressing Challenge",
                    order_index: 2,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: "41f75965-624a-48ad-b51d-39eb346707c9",
                    block_type: "paragraph",
                    content: "The problem is a pressing one: many people who are incarcerated have untreated mental health conditions that exacerbate their criminal behavior, leading to a vicious cycle of incarceration and recidivism. In the US, it's estimated that over 50% of prisoners have a serious mental illness, yet prisons are often ill-equipped to provide adequate care.",
                    order_index: 3,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: "f26ac3a0-fc43-40ae-adfb-dd1891a0abc5",
                    block_type: "subheading",
                    content: "The Solution: Machine Learning and Targeted Outreach",
                    order_index: 4,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: "3b93029e-5de5-4b32-b1f9-8c802f1d872f",
                    block_type: "paragraph",
                    content: "To address this issue, the researchers used machine learning algorithms to identify individuals at high risk of reincarceration based on their criminal history, demographic characteristics, and social services data. They then developed targeted outreach programs to connect these individuals with vital support services, such as mental health treatment and housing assistance.",
                    order_index: 5,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: "ca609c0b-c597-4626-a1fc-b7c4cffe2640",
                    block_type: "image",
                    content: `https://picsum.photos/800/400?random=${articleId}`,
                    caption: "Researchers analyzing data to identify high-risk individuals",
                    order_index: 6,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: "d3ff9b0b-e2b1-4c1a-a015-b615f644021e",
                    block_type: "subheading",
                    content: "Promising Results",
                    order_index: 7,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    block_type: "paragraph",
                    content: "The study involved a field trial in which the researchers worked with county agencies to identify over 1,000 individuals who were at high risk of reincarceration. These individuals received personalized outreach and support from caseworkers, who helped them access essential services and connect with community-based organizations.",
                    order_index: 8,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: "b2c3d4e5-f6a7-8901-bcde-f23456789012",
                    block_type: "quote",
                    content: "Among the highest-risk group, 55% of participants returned to jail within a year, compared to just 25% in a control group.",
                    order_index: 9,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: "c3d4e5f6-a7b8-9012-cdef-345678901234",
                    block_type: "paragraph",
                    content: "The results are promising: the study found that targeted outreach was most effective for individuals who had previously been incarcerated multiple times and had complex needs.",
                    order_index: 10,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: "d4e5f6a7-b8c9-0123-defa-456789012345",
                    block_type: "subheading",
                    content: "Implications for Policy",
                    order_index: 11,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: "e5f6a7b8-c9d0-1234-efab-567890123456",
                    block_type: "paragraph",
                    content: "The approach has important implications for criminal justice policy. By identifying high-risk individuals and providing them with tailored support services, it may be possible to reduce reincarceration rates and improve public safety. The researchers hope that their work will inform the development of similar programs in other jurisdictions.",
                    order_index: 12,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: "f6a7b8c9-d0e1-2345-fabc-678901234567",
                    block_type: "list",
                    items: [
                        "Identify high-risk individuals using data-driven methods",
                        "Provide personalized outreach and support services",
                        "Connect individuals with mental health treatment",
                        "Assist with housing and community resources",
                        "Monitor progress and adjust interventions as needed"
                    ],
                    order_index: 13,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                },
                {
                    id: "a7b8c9d0-e1f2-3456-abcd-789012345678",
                    block_type: "paragraph",
                    content: "As the US continues to grapple with issues related to mass incarceration and racial disparities in the criminal justice system, this study offers a hopeful glimpse into a more effective and compassionate approach. By prioritizing support services and community-based solutions, it may be possible to break the cycle of incarceration and create a more just and equitable society for all.",
                    order_index: 14,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                }
            ],
        };
        return HttpResponse.json(createSuccessResponse(mockArticle), {status: 200});
    }),

    // GET /news/feed
    http.get(`${API_BASE_URL}/api/v1/news/feed`, async ({request}) => {
        const url = new URL(request.url);
        const page = parseInt(url.searchParams.get("page")) || 1;
        const limit = parseInt(url.searchParams.get("limit")) || 10;

        const mockArticles = Array.from({length: limit}, (_, index) => {
            const idx = (page - 1) * limit + index + 1;
            return {
                id: `feed-article-${idx}`,
                title: `News ${idx}: Important News Content`,
                summary: `This is a news summary containing key points for article ${idx}.`,
                content: `Full news content for article ${idx}.\nMultiple paragraphs included.`,
                source: `News Source ${idx}`,
                image_url: `https://picsum.photos/800/400?random=${idx}`,
                published_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
                categories: ["Technology", "Politics", "Economy"].slice(0, Math.floor(Math.random() * 3) + 1),
                url: `https://example.com/article/${idx}`,
                author: `Author ${idx}`,
                reading_time: Math.floor(Math.random() * 10) + 3,
            };
        });

        return HttpResponse.json(
            createSuccessResponse({
                articles: mockArticles,
                pagination: {
                    page,
                    limit,
                    total: 100,
                    total_pages: Math.ceil(100 / limit),
                    has_next: page < Math.ceil(100 / limit),
                    has_prev: page > 1,
                },
            }),
            {status: 200}
        );
    }),

    // ------------------- Fields & Interests API -------------------

    // GET /api/v1/fields/ - Get all available fields and subfields
    http.get(`${API_BASE_URL}/api/v1/fields/`, () => {
        return HttpResponse.json(createSuccessResponse(FIELDS), {status: 200});
    }),

    // GET /api/v1/interests/ - Get user's selected interests
    http.get(`${API_BASE_URL}/api/v1/interests/`, () => {
        isLoggedIn = getLoginState();
        if (!isLoggedIn) {
            return HttpResponse.json(
                {code: 401, title: "AuthenticationError", message: "Not authenticated"},
                {status: 401}
            );
        }

        // Convert the Set of IDs back to the field/subfield structure
        const userInterests = [];
        FIELDS.forEach(field => {
            const selectedSubfields = field.subfields.filter(sf => mockUserInterestIds.has(sf.id));

            if (mockUserInterestIds.has(field.id)) {
                // User selected the whole field - return with all subfields
                userInterests.push({
                    id: field.id,
                    code: field.code,
                    name: field.name,
                    sort_order: field.sort_order,
                    subfields: field.subfields
                });
            } else if (selectedSubfields.length > 0) {
                // User selected only specific subfields
                userInterests.push({
                    id: field.id,
                    code: field.code,
                    name: field.name,
                    sort_order: field.sort_order,
                    subfields: selectedSubfields
                });
            }
        });

        return HttpResponse.json(createSuccessResponse(userInterests), {status: 200});
    }),

    // POST /api/v1/interests/ - Add an interest (field or subfield)
    http.post(`${API_BASE_URL}/api/v1/interests/`, async ({request}) => {
        isLoggedIn = getLoginState();
        if (!isLoggedIn) {
            return HttpResponse.json(
                {code: 401, title: "AuthenticationError", message: "Not authenticated"},
                {status: 401}
            );
        }

        const body = await request.json();
        const {field_id} = body || {};

        if (!field_id) {
            return HttpResponse.json(
                {code: 422, title: "Validation Error", message: "field_id is required"},
                {status: 422}
            );
        }

        // Check if field_id exists in our FIELDS
        const isValidField = FIELDS.some(f => f.id === field_id || f.subfields.some(sf => sf.id === field_id));
        if (!isValidField) {
            return HttpResponse.json(
                {code: 400, title: "APIError", message: "Invalid user_id or field_id"},
                {status: 400}
            );
        }

        // Check if already added
        if (mockUserInterestIds.has(field_id)) {
            return HttpResponse.json(
                {code: 409, title: "DuplicateInterestError", message: "Interest already added"},
                {status: 409}
            );
        }

        mockUserInterestIds.add(field_id);
        return HttpResponse.json(
            createSuccessResponse({
                message: `Successfully added interest for field ${field_id} and user ${mockUser.id}`
            }),
            {status: 200}
        );
    }),

    // DELETE /api/v1/interests/ - Remove an interest (field or subfield)
    http.delete(`${API_BASE_URL}/api/v1/interests/`, async ({request}) => {
        isLoggedIn = getLoginState();
        if (!isLoggedIn) {
            return HttpResponse.json(
                {code: 401, title: "AuthenticationError", message: "Not authenticated"},
                {status: 401}
            );
        }

        const body = await request.json();
        const {field_id} = body || {};

        if (!field_id) {
            return HttpResponse.json(
                {code: 422, title: "Validation Error", message: "field_id is required"},
                {status: 422}
            );
        }

        if (!mockUserInterestIds.has(field_id)) {
            return HttpResponse.json(
                {code: 400, title: "APIError", message: "Interest not found"},
                {status: 400}
            );
        }

        mockUserInterestIds.delete(field_id);
        return HttpResponse.json(
            createSuccessResponse({
                message: `Successfully removed field ${field_id} from user's interest`
            }),
            {status: 200}
        );
    }),

    // ------------------- Bookmarks API -------------------

    // POST /api/v1/bookmarks/ - Add bookmark
    http.post(`${API_BASE_URL}/api/v1/bookmarks/`, async ({request}) => {
        isLoggedIn = getLoginState();
        if (!isLoggedIn) {
            return HttpResponse.json(createErrorResponse("Unauthorized", "User not authenticated", 401), {status: 401});
        }

        const {article_id} = await request.json();
        if (!article_id) {
            return HttpResponse.json(createErrorResponse("BadRequest", "article_id is required", 400), {status: 400});
        }

        // Check if already bookmarked
        const existingBookmark = mockBookmarks.find(b => b.article_id === article_id);
        if (existingBookmark) {
            return HttpResponse.json(createErrorResponse("Conflict", "Article already bookmarked", 409), {status: 409});
        }

        const newBookmark = {
            id: `bookmark-${Date.now()}`,
            article_id,
            user_id: mockUser.id,
            created_at: new Date().toISOString(),
        };

        mockBookmarks.push(newBookmark);
        setBookmarks(mockBookmarks);
        return HttpResponse.json(createSuccessResponse(newBookmark), {status: 201});
    }),

    // DELETE /api/v1/bookmarks/by-article/:articleId - Remove bookmark
    http.delete(`${API_BASE_URL}/api/v1/bookmarks/by-article/:articleId`, async ({params}) => {
        isLoggedIn = getLoginState();
        if (!isLoggedIn) {
            return HttpResponse.json(createErrorResponse("Unauthorized", "User not authenticated", 401), {status: 401});
        }

        const {articleId} = params;
        const bookmarkIndex = mockBookmarks.findIndex(b => b.article_id === articleId);

        if (bookmarkIndex === -1) {
            return HttpResponse.json(createErrorResponse("NotFound", "Bookmark not found", 404), {status: 404});
        }

        mockBookmarks.splice(bookmarkIndex, 1);
        setBookmarks(mockBookmarks);
        return new HttpResponse(null, {status: 204});
    }),

    // GET /api/v1/bookmarks/ - Get user bookmarks
    http.get(`${API_BASE_URL}/api/v1/bookmarks/`, async () => {
        isLoggedIn = getLoginState();
        if (!isLoggedIn) {
            return HttpResponse.json(createErrorResponse("Unauthorized", "User not authenticated", 401), {status: 401});
        }

        // Get fresh bookmarks from localStorage
        mockBookmarks = getBookmarks();

        // Create mock articles for each bookmark
        const bookmarkedArticles = mockBookmarks.map((bookmark, index) => ({
            id: bookmark.article_id,
            title: `Bookmarked Article ${index + 1}`,
            description: `This is a bookmarked article with ID ${bookmark.article_id}`,
            keywords: ["bookmarked", "saved", "favorite"],
            slug: `bookmarked-article-${bookmark.article_id}`,
            featured_image_url: `https://picsum.photos/800/400?random=${bookmark.article_id}`,
            view_count: Math.floor(Math.random() * 1000),
            created_at: bookmark.created_at,
            updated_at: bookmark.created_at,
            is_bookmarked: false,
        }));

        return HttpResponse.json(createSuccessResponse(bookmarkedArticles), {status: 200});
    }),
];

