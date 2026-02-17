import { Skeleton } from "@/components/ui/skeleton";

export function RepositoryListSkeleton() {
    return (
        <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
                <div key={i} className="border rounded-lg p-6 space-y-3">
                    <div className="flex items-center justify-between">
                        <Skeleton className="h-6 w-64" />
                        <Skeleton className="h-8 w-20" />
                    </div>
                    <Skeleton className="h-4 w-full" />
                    <div className="flex gap-4">
                        <Skeleton className="h-4 w-20" />
                        <Skeleton className="h-4 w-20" />
                        <Skeleton className="h-4 w-32" />
                    </div>
                </div>
            ))}
        </div>
    );
}

export function ChatMessageSkeleton() {
    return (
        <div className="space-y-4">
            {[...Array(2)].map((_, i) => (
                <div key={i} className="flex gap-3">
                    <Skeleton className="h-10 w-10 rounded-full" />
                    <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-5/6" />
                    </div>
                </div>
            ))}
        </div>
    );
}

export function DashboardSkeleton() {
    return (
        <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="border rounded-lg p-6 space-y-3">
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-8 w-16" />
                        <Skeleton className="h-3 w-32" />
                    </div>
                ))}
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <div className="border rounded-lg p-6 space-y-4">
                    <Skeleton className="h-6 w-48" />
                    <div className="space-y-3">
                        {[...Array(5)].map((_, i) => (
                            <div key={i} className="flex items-center gap-3">
                                <Skeleton className="h-12 w-12 rounded" />
                                <div className="flex-1 space-y-2">
                                    <Skeleton className="h-4 w-3/4" />
                                    <Skeleton className="h-3 w-1/2" />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="border rounded-lg p-6 space-y-4">
                    <Skeleton className="h-6 w-48" />
                    <Skeleton className="h-64 w-full" />
                </div>
            </div>
        </div>
    );
}

export function AnalyticsSkeleton() {
    return (
        <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-3">
                {[...Array(3)].map((_, i) => (
                    <div key={i} className="border rounded-lg p-6 space-y-3">
                        <Skeleton className="h-4 w-32" />
                        <Skeleton className="h-10 w-20" />
                    </div>
                ))}
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <div className="border rounded-lg p-6 space-y-4">
                    <Skeleton className="h-6 w-40" />
                    <Skeleton className="h-80 w-full" />
                </div>
                <div className="border rounded-lg p-6 space-y-4">
                    <Skeleton className="h-6 w-40" />
                    <Skeleton className="h-80 w-full" />
                </div>
            </div>
        </div>
    );
}
