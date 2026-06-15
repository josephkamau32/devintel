import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { OrganizationWithRole, organizationsApi } from '../lib/api/organizations';
import { useAuth } from './AuthContext';

interface OrganizationContextType {
    organizations: OrganizationWithRole[];
    currentOrganization: OrganizationWithRole | null;
    isLoading: boolean;
    error: string | null;
    setCurrentOrganizationId: (orgId: string | null) => void;
    refreshOrganizations: () => Promise<void>;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

export const OrganizationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const { user, isAuthenticated } = useAuth();

    const [organizations, setOrganizations] = useState<OrganizationWithRole[]>([]);
    const [currentOrgId, setCurrentOrgId] = useState<string | null>(
        localStorage.getItem('currentOrgId')
    );
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const refreshOrganizations = useCallback(async () => {
        if (!isAuthenticated) {
            setOrganizations([]);
            return;
        }

        setIsLoading(true);
        setError(null);
        try {
            const orgs = await organizationsApi.listUserOrganizations();
            setOrganizations(orgs);

            // If current org is no longer in the list, reset to personal
            if (currentOrgId && !orgs.find((org) => org.id === currentOrgId)) {
                setCurrentOrganizationId(null);
            }
        } catch (err: unknown) {
            console.error('Failed to fetch organizations:', err);
            setError('Failed to load organizations. Please try again.');
        } finally {
            setIsLoading(false);
        }
    }, [isAuthenticated, currentOrgId]);

    useEffect(() => {
        if (isAuthenticated) {
            refreshOrganizations();
        }
    }, [isAuthenticated, refreshOrganizations]);

    const setCurrentOrganizationId = (orgId: string | null) => {
        setCurrentOrgId(orgId);
        if (orgId) {
            localStorage.setItem('currentOrgId', orgId);
        } else {
            localStorage.removeItem('currentOrgId');
        }
        // Optional: trigger a refresh of other data if needed
    };

    const currentOrganization = currentOrgId
        ? organizations.find(org => org.id === currentOrgId) || null
        : null;

    return (
        <OrganizationContext.Provider
            value={{
                organizations,
                currentOrganization,
                isLoading,
                error,
                setCurrentOrganizationId,
                refreshOrganizations,
            }}
        >
            {children}
        </OrganizationContext.Provider>
    );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useOrganization = () => {
    const context = useContext(OrganizationContext);
    if (context === undefined) {
        throw new Error('useOrganization must be used within an OrganizationProvider');
    }
    return context;
};
