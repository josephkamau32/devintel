import { useState } from "react";
import { useOrganization } from "@/contexts/OrganizationContext";
import { organizationsApi, OrganizationCreate, OrganizationWithRole } from "@/lib/api/organizations";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Building2, Plus, Users, Settings as SettingsIcon, LogOut } from "lucide-react";
import { OrganizationMembers } from "@/components/organizations/OrganizationMembers";

export default function OrganizationsSettings() {
    const userStr = localStorage.getItem('user');
    const user = userStr ? JSON.parse(userStr) : null;
    const {
        organizations,
        currentOrganization,
        setCurrentOrganizationId,
        refreshOrganizations,
        isLoading
    } = useOrganization();

    const [isCreating, setIsCreating] = useState(false);
    const [newOrgName, setNewOrgName] = useState("");
    const [managingOrgId, setManagingOrgId] = useState<string | null>(null);

    const handleCreateOrganization = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newOrgName.trim()) return;

        try {
            setIsCreating(true);
            const newOrg = await organizationsApi.create({ name: newOrgName });
            toast.success(`Organization "${newOrg.name}" created successfully`);
            setNewOrgName("");
            await refreshOrganizations();
            // Auto-switch to the new org
            setCurrentOrganizationId(newOrg.id);
        } catch (error: any) {
            toast.error(error.response?.data?.detail || "Failed to create organization");
        } finally {
            setIsCreating(false);
        }
    };

    const handleLeaveOrganization = async (orgId: string, orgName: string) => {
        if (!confirm(`Are you sure you want to leave ${orgName}?`)) return;

        try {
            if (!user) return;
            await organizationsApi.removeMember(orgId, user.id);
            toast.success(`Successfully left ${orgName}`);

            if (currentOrganization?.id === orgId) {
                setCurrentOrganizationId(null);
            }

            refreshOrganizations();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || "Failed to leave organization");
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-semibold tracking-tight">Organizations</h2>
                <p className="text-sm text-muted-foreground mt-1">
                    Create and manage organizations to collaborate on repositories with your team.
                </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                {/* Create Organization Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-lg">
                            <Plus className="h-5 w-5" />
                            New Organization
                        </CardTitle>
                        <CardDescription>
                            Create a new shared workspace for your team.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleCreateOrganization} className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="orgName">Organization Name</Label>
                                <Input
                                    id="orgName"
                                    placeholder="e.g. Acme Corp"
                                    value={newOrgName}
                                    onChange={(e) => setNewOrgName(e.target.value)}
                                    disabled={isCreating}
                                    required
                                />
                            </div>
                            <Button type="submit" disabled={isCreating || !newOrgName.trim()}>
                                {isCreating ? "Creating..." : "Create Organization"}
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                {/* List of Organizations */}
                <div className="space-y-4">
                    <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                        <Building2 className="h-4 w-4" />
                        Your Organizations
                    </h3>

                    {isLoading ? (
                        <div className="flex justify-center p-8">
                            <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full" />
                        </div>
                    ) : organizations.length === 0 ? (
                        <Card className="border-dashed bg-transparent">
                            <CardContent className="flex flex-col items-center justify-center p-6 text-center text-muted-foreground h-40">
                                <Building2 className="h-8 w-8 mb-2 opacity-50" />
                                <p>You don't belong to any organizations yet.</p>
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="space-y-3">
                            {organizations.map((org) => (
                                <Card key={org.id} className={currentOrganization?.id === org.id ? 'border-primary shadow-sm' : ''}>
                                    <CardHeader className="p-4 pb-2">
                                        <div className="flex items-center justify-between">
                                            <CardTitle className="text-base flex items-center gap-2">
                                                {org.name}
                                                {org.role === 'owner' && (
                                                    <span className="text-[10px] uppercase font-bold tracking-wider bg-primary/10 text-primary px-2 py-0.5 rounded-full">Owner</span>
                                                )}
                                                {org.role === 'admin' && (
                                                    <span className="text-[10px] uppercase font-bold tracking-wider bg-blue-500/10 text-blue-500 px-2 py-0.5 rounded-full">Admin</span>
                                                )}
                                                {currentOrganization?.id === org.id && (
                                                    <span className="text-[10px] uppercase font-bold tracking-wider bg-green-500/10 text-green-500 px-2 py-0.5 rounded-full flex items-center gap-1">
                                                        <span className="h-1.5 w-1.5 rounded-full bg-green-500"></span> Active
                                                    </span>
                                                )}
                                            </CardTitle>
                                        </div>
                                    </CardHeader>
                                    <CardContent className="p-4 pt-0">
                                        <div className="flex items-center justify-between mt-4">
                                            <Button
                                                variant={currentOrganization?.id === org.id ? "secondary" : "outline"}
                                                size="sm"
                                                onClick={() => setCurrentOrganizationId(org.id)}
                                                disabled={currentOrganization?.id === org.id}
                                            >
                                                {currentOrganization?.id === org.id ? "Currently Active" : "Switch To"}
                                            </Button>

                                            <div className="flex gap-2">
                                                <Button variant="ghost" size="icon" title="Organization Settings" disabled={org.role === 'member'}>
                                                    <SettingsIcon className="h-4 w-4 text-muted-foreground" />
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    title="Manage Members"
                                                    disabled={org.role === 'member'}
                                                    onClick={() => setManagingOrgId(org.id)}
                                                >
                                                    <Users className="h-4 w-4 text-muted-foreground" />
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                                                    title="Leave Organization"
                                                    onClick={() => handleLeaveOrganization(org.id, org.name)}
                                                    disabled={org.role === 'owner'} // Owners should delete or transfer, not just leave usually, handle better later
                                                >
                                                    <LogOut className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {managingOrgId && (
                <OrganizationMembers
                    organizationId={managingOrgId}
                    organizationName={organizations.find(o => o.id === managingOrgId)?.name || ""}
                    currentUserRole={organizations.find(o => o.id === managingOrgId)?.role || "member"}
                    open={!!managingOrgId}
                    onOpenChange={(open) => !open && setManagingOrgId(null)}
                />
            )}
        </div>
    );
}
