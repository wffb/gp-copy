import {useEffect, useState} from 'react';
import {Helmet} from 'react-helmet-async';
import {useNavigate} from 'react-router-dom';
import {api} from '@/services/api';
import Header from '@/components/Header/Header';
import {Button} from '@/components/ui/button';
import {ArrowLeft} from 'lucide-react';

export default function InterestsSettings() {
    const navigate = useNavigate();
    const [fields, setFields] = useState([]);           // 所有可选项（树）
    const [selectedIds, setSelectedIds] = useState(new Set()); // 已选（id 集合）
    const [busyId, setBusyId] = useState(null);         // 正在提交的那个 id（节流禁用）
    const [error, setError] = useState('');

    // 加载：先拉可选项，再拉已选项
    useEffect(() => {
        let mounted = true;

        (async () => {
            try {
                const resFields = await api.getFields();
                const all = resFields.data?.data ?? [];
                if (mounted) setFields(all);
            } catch {
                if (mounted) setError('Failed to load fields.');
            }

            try {
                const resMine = await api.getInterests();
                const mine = resMine.data?.data ?? [];
                // 把用户已选的 field 与 subfield 的 id 都纳入
                const acc = new Set();
                for (const f of mine) {
                    if (f?.id) acc.add(f.id);
                    for (const sf of f?.subfields ?? []) {
                        if (sf?.id) acc.add(sf.id);
                    }
                }
                if (mounted) setSelectedIds(acc);
            } catch {
                if (mounted) setError((prev) => prev || 'Failed to load interests.');
            }
        })();

        return () => {
            mounted = false;
        };
    }, []);

    // 切换单个 id（即点即更）
    const toggleOne = async (id) => {
        if (!id || busyId) return;
        setBusyId(id);
        setError('');
        try {
            if (selectedIds.has(id)) {
                await api.removeInterest(id);
                setSelectedIds((prev) => {
                    const next = new Set(prev);
                    next.delete(id);
                    return next;
                });
            } else {
                await api.addInterest(id);
                setSelectedIds((prev) => new Set(prev).add(id));
            }
        } catch (e) {
            // 处理常见错误码
            const code = e?.response?.data?.code;
            if (code === 401) setError('Not authenticated. Please log in.');
            else if (code === 409) setError('Already added.');
            else if (code === 400 || code === 422) setError(e?.response?.data?.message || 'Bad request.');
            else setError('Network error.');
        } finally {
            setBusyId(null);
        }
    };

    const isChecked = (id) => selectedIds.has(id);

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
            <Helmet><title>Interests Settings</title></Helmet>
            <Header/>

            {/* Back to Articles Button */}
            <div className="max-w-4xl mx-auto px-6 pt-8">
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
            <main className="max-w-4xl mx-auto px-6 py-8">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8 transition-colors">
                    <h1 className="text-2xl font-semibold mb-6 text-gray-900 dark:text-white">Interests</h1>

                    {error && (
                        <div
                            className="p-3 rounded border border-red-300 dark:border-red-600 text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/20 mb-6">
                            {error}
                        </div>
                    )}

                    {/* 三列网格展示：左 field / 右 subfields */}
                    <div className="grid md:grid-cols-3 gap-8">
                        {fields.map((group) => (
                            <div key={group.id} className="space-y-2">
                                <label className="flex items-center gap-2 font-semibold text-gray-900 dark:text-white">
                                    <input
                                        type="checkbox"
                                        disabled={busyId === group.id}
                                        checked={isChecked(group.id)}
                                        onChange={() => toggleOne(group.id)}
                                        className="rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700"
                                    />
                                    {group.name}
                                </label>

                                <div className="space-y-2 pl-6">
                                    {(group.subfields ?? []).map((sf) => (
                                        <label key={sf.id}
                                               className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                                            <input
                                                type="checkbox"
                                                disabled={busyId === sf.id}
                                                checked={isChecked(sf.id)}
                                                onChange={() => toggleOne(sf.id)}
                                                className="rounded border-gray-300 dark:border-gray-600 dark:bg-gray-700"
                                            />
                                            {sf.name}
                                        </label>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* 可选：批量操作区域（目前即点即更，不需要"保存"按钮） */}
                    <div className="flex gap-3 mt-6">
                        <button
                            className="px-3 py-2 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-900 dark:text-white"
                            onClick={() => setSelectedIds(new Set())}
                            type="button"
                        >
                            Clear (local)
                        </button>
                        <span className="text-xs text-gray-500 dark:text-gray-400 self-center">
          Selections are saved immediately when you toggle.
        </span>
                    </div>
                </div>
            </main>
        </div>
    );
}
