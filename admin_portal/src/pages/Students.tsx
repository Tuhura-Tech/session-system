import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Users } from "lucide-react";
import Sidebar from "../components/Sidebar";
import Layout from "../components/Layout";
import { adminApi } from "../services/api";
import type { ChildDetails } from "../types";

const Students: React.FC = () => {
  const [children, setChildren] = useState<ChildDetails[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    loadChildren();
  }, []);

  const loadChildren = async () => {
    try {
      setIsLoading(true);
      const data = await adminApi.listChildren();
      setChildren(data);
    } catch (error) {
      console.error("Failed to load children:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredChildren = children.filter((child) =>
    child.name.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1">
        <Layout title="Student Management">
          <div className="bg-white rounded-lg shadow p-4 mb-6">
            <input
              type="text"
              placeholder="Search students by name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            {isLoading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            ) : filteredChildren.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                <Users className="w-12 h-12 mb-4 opacity-50" />
                <p>
                  {searchTerm
                    ? "No students matching your search."
                    : "No students found."}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Date of Birth
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Media Consent
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredChildren.map((child) => (
                      <tr key={child.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {child.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {child.dateOfBirth
                            ? new Date(child.dateOfBirth).toLocaleDateString(
                                "en-NZ",
                                {
                                  day: "2-digit",
                                  month: "2-digit",
                                  year: "numeric",
                                },
                              )
                            : "—"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {child.mediaConsent ? (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              Yes
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                              No
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={() => navigate(`/children/${child.id}`)}
                            className="text-blue-600 hover:text-blue-900 font-medium"
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </Layout>
      </div>
    </div>
  );
};

export default Students;
