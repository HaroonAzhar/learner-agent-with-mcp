'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import api from '@/lib/api';
import { ArrowLeft, LogOut, BookOpen, Layers } from 'lucide-react';

interface Class {
    id: number;
    name: string;
    course_name: string;
}

export default function ClassDashboard() {
    const router = useRouter();
    const params = useParams();
    const classId = params.classId;

    const [user, setUser] = useState<any>(null);
    const [classData, setClassData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    const [resources, setResources] = useState<any[]>([]);
    const [assignments, setAssignments] = useState<any[]>([]);
    const [uploading, setUploading] = useState(false);

    // Upload Modal State
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [newResourceTitle, setNewResourceTitle] = useState('');
    const [newResourceType, setNewResourceType] = useState('video');
    const [newResourceFile, setNewResourceFile] = useState<File | null>(null);

    const fetchClassDetails = async () => {
        try {
            const [usersRes, classesRes, resourcesRes] = await Promise.all([
                api.get('/auth/users/me'),
                api.get('/teacher/classes'),
                api.get(`/teacher/classes/${classId}/resources`)
            ]);

            if (usersRes.data.role !== 'teacher' && usersRes.data.role !== 'admin') {
                router.push('/login');
                return;
            }
            setUser(usersRes.data);

            const foundClass = classesRes.data.find((c: Class) => c.id === parseInt(classId as string));
            if (!foundClass) {
                alert('You do not have access to this class');
                router.push('/teacher');
                return;
            }
            setClassData(foundClass);
            setResources(resourcesRes.data);

        } catch (err) {
            console.error(err);
            router.push('/login');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!classId) return;
        fetchClassDetails();
    }, [router, classId]);

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newResourceFile || !classId) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('title', newResourceTitle);
        formData.append('type', newResourceType);
        formData.append('class_id', classId as string);
        formData.append('file', newResourceFile);

        try {
            await api.post('/teacher/resources', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setShowUploadModal(false);
            setNewResourceTitle('');
            setNewResourceFile(null);
            // Refresh resources
            const res = await api.get(`/teacher/classes/${classId}/resources`);
            setResources(res.data);
            alert('Resource uploaded successfully! Analysis started.');
        } catch (err) {
            console.error(err);
            alert('Failed to upload resource');
        } finally {
            setUploading(false);
        }
    };

    if (loading) return <div className="p-8 flex justify-center text-gray-500">Loading Dashboard...</div>;

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Navbar */}
            <nav className="bg-white shadow-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16 items-center">
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => router.push('/teacher')}
                                className="text-gray-500 hover:text-gray-700 transition-colors"
                            >
                                <ArrowLeft size={20} />
                            </button>
                            <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                                <BookOpen className="w-5 h-5 text-blue-600" />
                                {classData?.name} <span className="text-gray-400 font-normal">| {classData?.course_name}</span>
                            </h1>
                        </div>
                        <div className="flex items-center gap-4">
                            <span className="text-gray-600">Welcome, {user?.username}</span>
                            <button
                                onClick={() => {
                                    localStorage.removeItem('token');
                                    router.push('/login');
                                }}
                                className="text-red-500 hover:text-red-700 text-sm font-medium flex items-center gap-1"
                            >
                                <LogOut size={16} />
                                Sign Out
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Main Content Area */}
                    <div className="lg:col-span-2 space-y-8">
                        {/* Resources Section */}
                        <div className="bg-white rounded-lg shadow-sm p-6">
                            <div className="flex justify-between items-center mb-6">
                                <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                                    <Layers size={20} className="text-blue-500" />
                                    Class Resources
                                </h2>
                                <button
                                    onClick={() => setShowUploadModal(true)}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm flex items-center gap-2"
                                >
                                    + Add Resource
                                </button>
                            </div>

                            {resources.length === 0 ? (
                                <div className="border-2 border-dashed border-gray-200 rounded-lg p-8 text-center text-gray-500">
                                    No resources uploaded yet.
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {resources.map((resource) => (
                                        <div key={resource.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <h3 className="font-semibold text-gray-900">{resource.title}</h3>
                                                    <p className="text-sm text-gray-500 capitalize">{resource.type}</p>
                                                </div>
                                                <button
                                                    onClick={() => router.push(`/teacher/labs/${resource.id}`)}
                                                    className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium hover:bg-green-200"
                                                >
                                                    Open Lab
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Assignments Section (Placeholder) */}
                        <div className="bg-white rounded-lg shadow-sm p-6 opacity-50">
                            <h2 className="text-lg font-bold text-gray-900 mb-4">Assignments</h2>
                            <div className="border-2 border-dashed border-gray-200 rounded-lg p-8 text-center text-gray-500">
                                Feature coming soon...
                            </div>
                        </div>
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        <div className="bg-white rounded-lg shadow-sm p-6">
                            <h3 className="font-semibold text-gray-900 mb-2">Class Overview</h3>
                            <p className="text-sm text-gray-500 mb-4">
                                Manage your class resources and assignments from here. Uploading resources triggers the Learner Agent to analyze content automatically.
                            </p>
                            <div className="text-xs text-gray-400">
                                Class ID: {classId}
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            {/* Upload Modal */}
            {showUploadModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Upload New Resource</h2>
                        <form onSubmit={handleUpload} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                                <input
                                    type="text"
                                    required
                                    value={newResourceTitle}
                                    onChange={(e) => setNewResourceTitle(e.target.value)}
                                    className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
                                    placeholder="e.g., Week 1 - Intro to AI"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                                <select
                                    value={newResourceType}
                                    onChange={(e) => setNewResourceType(e.target.value)}
                                    className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
                                >
                                    <option value="video">Video</option>
                                    <option value="pdf">PDF</option>
                                    <option value="article">Article</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">File</label>
                                <input
                                    type="file"
                                    required
                                    onChange={(e) => setNewResourceFile(e.target.files ? e.target.files[0] : null)}
                                    className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                                />
                            </div>
                            <div className="flex justify-end gap-3 mt-6">
                                <button
                                    type="button"
                                    onClick={() => setShowUploadModal(false)}
                                    className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={uploading}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                                >
                                    {uploading ? 'Uploading...' : 'Upload'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
