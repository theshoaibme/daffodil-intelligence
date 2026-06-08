import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  Loader2,
  FileText,
  Lock,
  LogOut,
  Pencil,
  Shield,
  User,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { changePassword, DELETE_ACCOUNT_PHRASE } from "../../lib/api";
import { ROUTES } from "../../lib/routes";
import { FIELD_CLASS } from "../../lib/formStyles";
import { dropdownPanelVariants } from "../../lib/motion";

interface ProfileForm {
  fullName: string;
  department: string;
  studentId: string;
  semester: string;
  avatarUrl: string;
}

function userInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return (parts[0]?.slice(0, 2) ?? "?").toUpperCase();
}

function displayName(fullName: string | null | undefined, email: string): string {
  if (fullName?.trim()) return fullName.trim();
  return email.split("@")[0] ?? email;
}

function profileFromUser(user: {
  full_name?: string | null;
  department?: string | null;
  student_id?: string | null;
  semester?: number | null;
  avatar_url?: string | null;
}): ProfileForm {
  return {
    fullName: user.full_name ?? "",
    department: user.department ?? "",
    studentId: user.student_id ?? "",
    semester: user.semester != null ? String(user.semester) : "",
    avatarUrl: user.avatar_url ?? "",
  };
}

const BATCH_ID_MIN = 1;
const BATCH_ID_MAX = 999;

function parseBatchId(raw: string): { value: number | null; error: string | null } {
  const trimmed = raw.trim();
  if (!trimmed) return { value: null, error: null };

  const num = Number(trimmed);
  if (!Number.isInteger(num) || Number.isNaN(num)) {
    return { value: null, error: "Batch ID must be a whole number." };
  }
  if (num < BATCH_ID_MIN || num > BATCH_ID_MAX) {
    return { value: null, error: `Batch ID must be between ${BATCH_ID_MIN} and ${BATCH_ID_MAX}.` };
  }
  return { value: num, error: null };
}

function formatMemberSince(value?: string): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString(undefined, { month: "long", year: "numeric" });
}

function AccountAvatar({
  avatarUrl,
  initials,
}: {
  avatarUrl?: string | null;
  initials: string;
}) {
  const [failed, setFailed] = useState(false);

  if (avatarUrl && !failed) {
    return (
      <img
        src={avatarUrl}
        alt=""
        referrerPolicy="no-referrer"
        className="w-20 h-20 rounded-full object-cover border border-outline-variant/30"
        onError={() => setFailed(true)}
      />
    );
  }

  return (
    <div className="w-20 h-20 rounded-full border border-outline-variant/30 bg-primary/15 flex items-center justify-center">
      <span className="text-2xl font-bold text-primary">{initials}</span>
    </div>
  );
}

function SectionCard({
  icon,
  title,
  action,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-outline-variant/40 bg-surface-container-lowest px-5 sm:px-6 py-5">
      <div className="flex items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
            {icon}
          </div>
          <h2 className="text-base font-semibold text-on-surface">{title}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-6 py-2.5">
      <span className="text-sm text-on-surface-variant">{label}</span>
      <span className="text-sm font-medium text-on-surface sm:text-right break-all">{value}</span>
    </div>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="block text-xs font-medium text-on-surface-variant mb-1.5">{children}</label>
  );
}

const inputClass = FIELD_CLASS;

const textButtonClass =
  "text-sm font-semibold text-primary hover:underline border-0 bg-transparent cursor-pointer p-0 disabled:opacity-40 disabled:cursor-not-allowed";

const cancelButtonClass =
  "px-5 py-2.5 rounded-full text-sm font-semibold text-on-surface-variant hover:bg-surface-container-high transition-colors border-0 cursor-pointer disabled:opacity-50";

const saveButtonClass =
  "inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-full bg-primary text-on-primary text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 border-0 cursor-pointer";

export function AccountPage() {
  const navigate = useNavigate();
  const { user, isLoading, updateProfile, deleteAccount, logout } = useAuth();

  const [profileForm, setProfileForm] = useState<ProfileForm>({
    fullName: "",
    department: "",
    studentId: "",
    semester: "",
    avatarUrl: "",
  });
  const [editingProfile, setEditingProfile] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileMessage, setProfileMessage] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  const [editingPassword, setEditingPassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [savingPassword, setSavingPassword] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteConfirmPhrase, setDeleteConfirmPhrase] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const resetProfileForm = useCallback(() => {
    if (!user) return;
    setProfileForm(profileFromUser(user));
  }, [user]);

  useEffect(() => {
    resetProfileForm();
  }, [resetProfileForm]);

  const name = useMemo(
    () => (user ? displayName(user.full_name, user.email) : ""),
    [user]
  );
  const initials = userInitials(name || "User");
  const memberSince = formatMemberSince(user?.created_at);
  const canDelete = deleteConfirmPhrase.trim() === DELETE_ACCOUNT_PHRASE;
  const passwordsMatch = newPassword === confirmPassword && newPassword.length >= 6;

  const handleCancelProfile = () => {
    resetProfileForm();
    setEditingProfile(false);
    setProfileMessage(null);
    setProfileError(null);
  };

  const handleSaveProfile = async () => {
    setProfileMessage(null);
    setProfileError(null);

    const { value: batchIdValue, error: batchIdError } = parseBatchId(profileForm.semester);
    if (batchIdError) {
      setProfileError(batchIdError);
      return;
    }

    setSavingProfile(true);
    try {
      await updateProfile({
        full_name: profileForm.fullName.trim() || null,
        department: profileForm.department.trim() || null,
        student_id: profileForm.studentId.trim() || null,
        semester: batchIdValue,
        avatar_url: profileForm.avatarUrl.trim() || null,
      });
      setEditingProfile(false);
      setProfileMessage("Profile updated.");
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : "Could not save profile.");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleCancelPassword = () => {
    setEditingPassword(false);
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setPasswordMessage(null);
    setPasswordError(null);
  };

  const handleSavePassword = async () => {
    if (!passwordsMatch) {
      setPasswordError("New passwords must match and be at least 6 characters.");
      return;
    }
    setSavingPassword(true);
    setPasswordMessage(null);
    setPasswordError(null);
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      handleCancelPassword();
      setPasswordMessage("Password updated successfully.");
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : "Could not update password.");
    } finally {
      setSavingPassword(false);
    }
  };

  const handleSignOut = () => {
    logout();
    navigate(ROUTES.login, { replace: true });
  };

  const handleDelete = async () => {
    if (!canDelete) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await deleteAccount({ confirmation_phrase: deleteConfirmPhrase.trim() });
      navigate(ROUTES.login, { replace: true });
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Could not delete account.");
      setDeleting(false);
    }
  };

  if (isLoading && !user) {
    return (
      <div className="min-h-screen bg-background text-on-surface flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background text-on-surface font-sans">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
        <button
          type="button"
          onClick={() => navigate(ROUTES.home)}
          className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline mb-8 border-0 bg-transparent cursor-pointer p-0"
        >
          <ArrowLeft size={16} />
          Back to workspace
        </button>

        <div className="flex items-center gap-5 mb-8">
          <AccountAvatar avatarUrl={user.avatar_url} initials={initials} />
          <div className="min-w-0">
            <h1 className="text-2xl font-semibold tracking-tight truncate">{name}</h1>
            <p className="text-sm text-on-surface-variant mt-0.5 truncate normal-case">{user.email}</p>
            {memberSince && (
              <p className="text-xs text-on-surface-variant/70 mt-1">Member since {memberSince}</p>
            )}
          </div>
        </div>

        <div className="space-y-5">
          <SectionCard
            icon={<User size={18} className="text-primary" />}
            title="Personal info"
            action={
              !editingProfile ? (
                <button
                  type="button"
                  onClick={() => {
                    setEditingProfile(true);
                    setProfileMessage(null);
                    setProfileError(null);
                  }}
                  className={`${textButtonClass} inline-flex items-center gap-1.5`}
                >
                  <Pencil size={14} />
                  Edit
                </button>
              ) : null
            }
          >
            {!editingProfile ? (
              <>
                <InfoRow label="Full name" value={profileForm.fullName || "—"} />
                <InfoRow label="Email" value={user.email} />
                <InfoRow label="Department" value={profileForm.department || "—"} />
                <InfoRow label="Student ID" value={profileForm.studentId || "—"} />
                <InfoRow label="Batch ID" value={profileForm.semester || "—"} />
                <InfoRow
                  label="Profile photo"
                  value={
                    profileForm.avatarUrl ? (
                      <a
                        href={profileForm.avatarUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        View photo
                      </a>
                    ) : (
                      "—"
                    )
                  }
                />
              </>
            ) : (
              <div className="space-y-4">
                <div>
                  <FieldLabel>Full name</FieldLabel>
                  <input
                    type="text"
                    value={profileForm.fullName}
                    onChange={(e) => setProfileForm((f) => ({ ...f, fullName: e.target.value }))}
                    className={inputClass}
                    autoComplete="name"
                  />
                </div>
                <div>
                  <FieldLabel>Email</FieldLabel>
                  <input type="email" value={user.email} readOnly className={`${inputClass} opacity-70 cursor-not-allowed`} />
                </div>
                <div>
                  <FieldLabel>Department</FieldLabel>
                  <input
                    type="text"
                    value={profileForm.department}
                    onChange={(e) => setProfileForm((f) => ({ ...f, department: e.target.value }))}
                    className={inputClass}
                    placeholder="e.g. CSE"
                  />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <FieldLabel>Student ID</FieldLabel>
                    <input
                      type="text"
                      value={profileForm.studentId}
                      onChange={(e) => setProfileForm((f) => ({ ...f, studentId: e.target.value }))}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <FieldLabel>Batch ID</FieldLabel>
                    <input
                      type="number"
                      min={BATCH_ID_MIN}
                      max={BATCH_ID_MAX}
                      value={profileForm.semester}
                      onChange={(e) => setProfileForm((f) => ({ ...f, semester: e.target.value }))}
                      className={inputClass}
                      placeholder="e.g. 64, 65, 67"
                    />
                  </div>
                </div>
                <div>
                  <FieldLabel>Profile photo URL</FieldLabel>
                  <input
                    type="url"
                    value={profileForm.avatarUrl}
                    onChange={(e) => setProfileForm((f) => ({ ...f, avatarUrl: e.target.value }))}
                    className={inputClass}
                    placeholder="https://..."
                  />
                </div>
                {profileError && (
                  <p className="text-sm text-error" role="alert">
                    {profileError}
                  </p>
                )}
                <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2 pt-2">
                  <button type="button" onClick={handleCancelProfile} disabled={savingProfile} className={cancelButtonClass}>
                    Cancel
                  </button>
                  <button type="button" onClick={handleSaveProfile} disabled={savingProfile} className={saveButtonClass}>
                    {savingProfile && <Loader2 size={14} className="animate-spin" />}
                    Save
                  </button>
                </div>
              </div>
            )}
            {profileMessage && !editingProfile && (
              <p className="text-sm text-primary mt-3" role="status">
                {profileMessage}
              </p>
            )}
          </SectionCard>

          <SectionCard
            icon={<Shield size={18} className="text-primary" />}
            title="Security"
            action={
              !editingPassword ? (
                <button
                  type="button"
                  onClick={() => {
                    setEditingPassword(true);
                    setPasswordMessage(null);
                    setPasswordError(null);
                  }}
                  className={`${textButtonClass} inline-flex items-center gap-1.5`}
                >
                  <Pencil size={14} />
                  Edit
                </button>
              ) : null
            }
          >
            {!editingPassword ? (
              <>
                <InfoRow label="Password" value="••••••••" />
                <InfoRow label="Account ID" value={`#${user.id}`} />
                <InfoRow label="Sign-in" value="Active on this device" />
                {passwordMessage && (
                  <p className="text-sm text-primary pt-2" role="status">
                    {passwordMessage}
                  </p>
                )}
                <button
                  type="button"
                  onClick={handleSignOut}
                  className="mt-4 inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-surface-container-highest hover:bg-surface-container-high text-sm font-semibold text-on-surface transition-colors border-0 cursor-pointer"
                >
                  <LogOut size={15} />
                  Sign out on this device
                </button>
              </>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-sm text-on-surface-variant">
                  <Lock size={15} className="text-primary" />
                  <span>Choose a strong password you do not use elsewhere.</span>
                </div>
                <div>
                  <FieldLabel>Current password</FieldLabel>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className={inputClass}
                    autoComplete="current-password"
                  />
                </div>
                <div>
                  <FieldLabel>New password</FieldLabel>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className={inputClass}
                    autoComplete="new-password"
                    minLength={6}
                  />
                </div>
                <div>
                  <FieldLabel>Confirm new password</FieldLabel>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={inputClass}
                    autoComplete="new-password"
                    minLength={6}
                  />
                </div>
                {passwordError && (
                  <p className="text-sm text-error" role="alert">
                    {passwordError}
                  </p>
                )}
                <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2 pt-2">
                  <button type="button" onClick={handleCancelPassword} disabled={savingPassword} className={cancelButtonClass}>
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleSavePassword}
                    disabled={savingPassword || !currentPassword || !passwordsMatch}
                    className={saveButtonClass}
                  >
                    {savingPassword && <Loader2 size={14} className="animate-spin" />}
                    Save
                  </button>
                </div>
              </div>
            )}
          </SectionCard>

          <SectionCard
            icon={<FileText size={18} className="text-primary" />}
            title="Data & privacy"
          >
            <div className="flex flex-wrap gap-4 text-sm">
              <Link to={ROUTES.privacy} className="text-primary hover:underline">
                Privacy Policy
              </Link>
              <Link to={ROUTES.terms} className="text-primary hover:underline">
                Terms of Service
              </Link>
            </div>
          </SectionCard>

          <section className="rounded-2xl border border-error/25 bg-error/5 p-5 sm:p-6">
            <div className="flex items-start gap-3">
              <AlertTriangle size={20} className="text-error flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <h2 className="text-base font-semibold text-on-surface">Delete your account</h2>
                <p className="text-sm text-on-surface-variant mt-1.5 leading-relaxed">
                  Permanently delete your account and all associated data, including chat history.
                  This action cannot be undone.
                </p>
                <button
                  type="button"
                  onClick={() => {
                    setDeleteOpen(true);
                    setDeleteConfirmPhrase("");
                    setDeleteError(null);
                  }}
                  className="mt-4 px-5 py-2.5 rounded-full bg-[#d93025] text-white text-sm font-semibold hover:bg-[#c5221f] transition-colors border-0 cursor-pointer"
                >
                  Delete account
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>

      <AnimatePresence>
        {deleteOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-background/70 backdrop-blur-sm"
            onClick={() => !deleting && setDeleteOpen(false)}
          >
            <motion.div
              variants={dropdownPanelVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              style={{ transformOrigin: "center center" }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-md rounded-2xl border border-outline-variant/40 bg-surface-container-lowest shadow-xl p-6 text-on-surface"
            >
              <h3 className="text-lg font-semibold">Delete your account?</h3>
              <p className="text-sm text-on-surface-variant mt-2 leading-relaxed">
                You will lose access to Daffodil Intelligence and your data will be permanently
                removed. This cannot be undone.
              </p>

              <div className="mt-5">
                <FieldLabel>
                  Type <span className="font-semibold text-on-surface">{DELETE_ACCOUNT_PHRASE}</span> to confirm
                </FieldLabel>
                <input
                  type="text"
                  value={deleteConfirmPhrase}
                  onChange={(e) => setDeleteConfirmPhrase(e.target.value)}
                  className={inputClass}
                  placeholder={DELETE_ACCOUNT_PHRASE}
                  autoComplete="off"
                  spellCheck={false}
                />
              </div>

              {deleteError && (
                <p className="mt-3 text-sm text-error" role="alert">
                  {deleteError}
                </p>
              )}

              <div className="mt-6 flex flex-col-reverse sm:flex-row sm:justify-end gap-2">
                <button
                  type="button"
                  disabled={deleting}
                  onClick={() => setDeleteOpen(false)}
                  className={cancelButtonClass}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={!canDelete || deleting}
                  onClick={handleDelete}
                  className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-full bg-[#d93025] text-white text-sm font-semibold hover:bg-[#c5221f] transition-colors border-0 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {deleting && <Loader2 size={14} className="animate-spin" />}
                  Delete account
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
