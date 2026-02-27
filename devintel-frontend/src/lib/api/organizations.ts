import apiClient from '../api-client';

export interface Organization {
    id: string;
    name: string;
    slug: string;
    created_at: string;
    updated_at: string;
    created_by: string;
}

export interface OrganizationCreate {
    name: string;
}

export interface OrganizationUpdate {
    name: string;
}

export interface OrganizationMember {
    org_id: string;
    user_id: string;
    role: 'owner' | 'admin' | 'member';
    joined_at: string;
    user?: {
        id: string;
        email: string;
        full_name: string;
        avatar_url: string;
    };
}

export interface OrganizationMemberCreate {
    user_id?: string;
    email?: string;
    github_username?: string;
    role: 'owner' | 'admin' | 'member';
}

export interface OrganizationMemberUpdate {
    role: 'owner' | 'admin' | 'member';
}

export interface OrganizationWithRole extends Organization {
    role: 'owner' | 'admin' | 'member';
}

export interface OrganizationDetail extends Organization {
    members: OrganizationMember[];
    repositories: any[]; // Replace with specific interface when available
}

export const organizationsApi = {
    // Organization operations
    create: (data: OrganizationCreate) => {
        return apiClient.post<Organization>('/api/v1/organizations/', data);
    },

    listUserOrganizations: () => {
        return apiClient.get<OrganizationWithRole[]>('/api/v1/organizations/');
    },

    get: (orgId: string) => {
        return apiClient.get<OrganizationDetail>(`/api/v1/organizations/${orgId}`);
    },

    update: (orgId: string, data: OrganizationUpdate) => {
        return apiClient.put<Organization>(`/api/v1/organizations/${orgId}`, data);
    },

    delete: (orgId: string) => {
        return apiClient.delete<{ message: string }>(`/api/v1/organizations/${orgId}`);
    },

    // Member operations
    listMembers: (orgId: string) => {
        return apiClient.get<OrganizationMember[]>(`/api/v1/organizations/${orgId}/members`);
    },

    addMember: (orgId: string, data: OrganizationMemberCreate) => {
        return apiClient.post<OrganizationMember>(`/api/v1/organizations/${orgId}/members`, data);
    },

    updateMemberRole: (orgId: string, userId: string, data: OrganizationMemberUpdate) => {
        return apiClient.put<OrganizationMember>(`/api/v1/organizations/${orgId}/members/${userId}/role`, data);
    },

    removeMember: (orgId: string, userId: string) => {
        return apiClient.delete<{ message: string }>(`/api/v1/organizations/${orgId}/members/${userId}`);
    },
};
