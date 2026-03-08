import { useState, useEffect, useCallback } from "react";
import { organizationsApi, OrganizationMember } from "@/lib/api/organizations";
import { useOrganization } from "@/contexts/OrganizationContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Loader2, Shield, ShieldAlert, User, Trash2 } from "lucide-react";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";

interface OrganizationMembersProps {
    organizationId: string;
    organizationName: string;
    currentUserRole: string;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function OrganizationMembers({
    organizationId,
    organizationName,
    currentUserRole,
    open,
    onOpenChange,
}: OrganizationMembersProps) {
    const [members, setMembers] = useState<OrganizationMember[]>([]);
    const [loading, setLoading] = useState(true);
    const [inviting, setInviting] = useState(false);
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteRole, setInviteRole] = useState<'admin' | 'member'>("member");
    const { refreshOrganizations } = useOrganization();

    const fetchMembers = useCallback(async () => {
        if (!open) return;
        try {
            setLoading(true);
            const data = await organizationsApi.listMembers(organizationId);
            setMembers(data);
        } catch (error) {
            toast.error("Failed to load members");
        } finally {
            setLoading(false);
        }
    }, [organizationId, open]);

    useEffect(() => {
        fetchMembers();
    }, [fetchMembers]);

    const handleInvite = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inviteEmail.trim()) return;

        try {
            setInviting(true);
            await organizationsApi.addMember(organizationId, {
                email: inviteEmail,
                role: inviteRole,
            });
            toast.success(`Invited ${inviteEmail} successfully`);
            setInviteEmail("");
            fetchMembers();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || "Failed to invite user");
        } finally {
            setInviting(false);
        }
    };

    const handleUpdateRole = async (userId: string, newRole: 'owner' | 'admin' | 'member') => {
        try {
            await organizationsApi.updateMemberRole(organizationId, userId, { role: newRole });
            toast.success("Role updated successfully");
            fetchMembers();
            refreshOrganizations(); // In case the current user's role changed
        } catch (error: unknown) {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || "Failed to update role");
        }
    };

    const handleRemoveMember = async (userId: string, name: string) => {
        if (!confirm(`Are you sure you want to remove ${name} from this organization?`)) return;

        try {
            await organizationsApi.removeMember(organizationId, userId);
            toast.success("Member removed successfully");
            fetchMembers();
        } catch (error: unknown) {
            const err = error as { response?: { data?: { detail?: string } } };
            toast.error(err.response?.data?.detail || "Failed to remove member");
        }
    };

    const canManageMembers = currentUserRole === 'owner' || currentUserRole === 'admin';

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle>Team Members - {organizationName}</DialogTitle>
                    <DialogDescription>
                        Manage who has access to this organization and its repositories.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-6 mt-4">
                    {/* Invite Section */}
                    {canManageMembers && (
                        <div className="rounded-lg border border-border bg-accent/30 p-4">
                            <h3 className="text-sm font-medium mb-3">Invite Member</h3>
                            <form onSubmit={handleInvite} className="flex items-end gap-3">
                                <div className="flex-1 space-y-1.5">
                                    <Label htmlFor="email" className="text-xs">Email Address</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        placeholder="colleague@example.com"
                                        value={inviteEmail}
                                        onChange={(e) => setInviteEmail(e.target.value)}
                                        className="h-9"
                                        required
                                    />
                                </div>
                                <div className="w-32 space-y-1.5">
                                    <Label className="text-xs">Role</Label>
                                    <Select value={inviteRole} onValueChange={(v: 'admin'|'member') => setInviteRole(v)}>
                                        <SelectTrigger className="h-9">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="member">Member</SelectItem>
                                            <SelectItem value="admin">Admin</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <Button type="submit" size="sm" className="h-9" disabled={inviting || !inviteEmail.trim()}>
                                    {inviting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Invite"}
                                </Button>
                            </form>
                        </div>
                    )}

                    {/* Members List */}
                    <div>
                        <h3 className="text-sm font-medium mb-3">Current Members</h3>
                        {loading ? (
                            <div className="flex justify-center py-8">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : (
                            <div className="rounded-md border border-border divide-y divide-border">
                                {members.map((member) => (
                                    <div key={member.user_id} className="flex items-center justify-between p-3">
                                        <div className="flex items-center gap-3">
                                            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-medium">
                                                {member.user?.full_name?.charAt(0) || member.user?.email.charAt(0)}
                                            </div>
                                            <div>
                                                <p className="text-sm font-medium text-foreground">
                                                    {member.user?.full_name || "Unknown User"}
                                                </p>
                                                <p className="text-xs text-muted-foreground">
                                                    {member.user?.email}
                                                </p>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-3">
                                            {/* Role Display/Edit */}
                                            {canManageMembers && member.role !== 'owner' ? (
                                                <Select
                                                    value={member.role}
                                                    onValueChange={(v: 'owner'|'admin'|'member') => handleUpdateRole(member.user_id, v)}
                                                >
                                                    <SelectTrigger className="h-8 w-[100px] text-xs">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="member" className="text-xs">Member</SelectItem>
                                                        <SelectItem value="admin" className="text-xs">Admin</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            ) : (
                                                <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-accent text-xs font-medium text-muted-foreground">
                                                    {member.role === 'owner' ? <ShieldAlert className="h-3.5 w-3.5 text-primary" /> : null}
                                                    {member.role === 'admin' ? <Shield className="h-3.5 w-3.5 text-blue-500" /> : null}
                                                    {member.role === 'member' ? <User className="h-3.5 w-3.5" /> : null}
                                                    <span className="capitalize">{member.role}</span>
                                                </div>
                                            )}

                                            {/* Remove Action */}
                                            {canManageMembers && member.role !== 'owner' && (
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                                                    onClick={() => handleRemoveMember(member.user_id, member.user?.full_name || member.user?.email || 'User')}
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
