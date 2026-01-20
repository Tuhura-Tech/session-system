import React, { useState } from "react";
import { Send } from "lucide-react";
import Modal from "./Modal";

interface BulkEmailModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSend: (content: string, status?: string) => Promise<void>;
}

const BulkEmailModal: React.FC<BulkEmailModalProps> = ({
  isOpen,
  onClose,
  onSend,
}) => {
  const [content, setContent] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("confirmed");
  const [isSending, setIsSending] = useState(false);

  const handleSend = async () => {
    if (!content.trim()) {
      alert("Please enter email content");
      return;
    }

    try {
      setIsSending(true);
      await onSend(content, selectedStatus);
      setContent("");
      setSelectedStatus("confirmed");
      onClose();
    } finally {
      setIsSending(false);
    }
  };

  return (
    <Modal isOpen={isOpen} title="Send Bulk Email" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Recipient Status
          </label>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="confirmed">Confirmed</option>
            <option value="waitlisted">Waitlisted</option>
            <option value="all">All</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email Content
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={8}
            placeholder="Type your email message here..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={isSending}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSend}
            disabled={isSending || !content.trim()}
            className="inline-flex items-center px-4 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            <Send className="w-4 h-4 mr-2" />
            {isSending ? "Sending..." : "Send Email"}
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default BulkEmailModal;
