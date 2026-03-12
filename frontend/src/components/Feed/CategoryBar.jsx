import React from 'react';
import {useNavigate} from 'react-router-dom';

const slugify = (name) =>
    (name || '')
        .toString()
        .toLowerCase()
        .trim()
        .replace(/\s+/g, '-')
        .replace(/[^a-z0-9-]/g, '');

export default function CategoryBar({categories = [], current /* string|null */}) {
    const navigate = useNavigate();
    const options = ['All', ...Array.from(new Set(categories)).filter(Boolean)];

    const currentSlug = current ? slugify(current) : '';  // '' 代表 All

    const goto = (label) => {
        if (label === 'All') navigate('/');
        else navigate(`/${slugify(label)}`);
    };

    return (
        <div className="w-full border-b border-gray-200 dark:border-gray-700 mb-8 transition-colors">
            <div className="flex flex-wrap justify-start gap-8 pb-3">
                {options.map((label) => {
                    const labelSlug = label === 'All' ? '' : slugify(label);
                    const selected = currentSlug === labelSlug;
                    const displayLabel = label === 'All' ? 'ALL' : label.toUpperCase();
                    return (
                        <button
                            key={label}
                            type="button"
                            onClick={() => goto(label)}
                            aria-pressed={selected}
                            className={
                                'text-sm font-medium tracking-wide transition-colors relative ' +
                                (selected
                                    ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400 pb-3'
                                    : 'text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white pb-3')
                            }
                        >
                            {displayLabel}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}

