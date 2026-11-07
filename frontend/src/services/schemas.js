import { z } from "zod";

const COMMON_PASSWORDS = new Set([
  "123456789012",
  "password1234",
  "passwordpassword",
  "qwertyuiop12",
  "letmein12345",
  "iloveyou1234",
  "welcome12345",
  "admin1234567",
  "abc123456789",
  "monkey123456",
]);

const EMAIL_MESSAGE = "Enter a valid email address.";

export const emailField = z
  .string()
  .trim()
  .min(1, "Enter your email address.")
  .max(254, "That email address is too long.")
  .email(EMAIL_MESSAGE)
  .transform((value) => value.toLowerCase());

export function passwordChecks(password, email = "") {
  const value = String(password ?? "");
  const local = String(email ?? "")
    .split("@")[0]
    .toLowerCase();

  return {
    length: value.length >= 12,
    notNumeric: value.length > 0 && !/^\d+$/.test(value),
    notCommon: value.length > 0 && !COMMON_PASSWORDS.has(value.toLowerCase()),
    notSimilar:
      value.length > 0 &&
      (local.length < 4 || !value.toLowerCase().includes(local.toLowerCase())),
  };
}

export function passwordProblemList(password, email = "") {
  const checks = passwordChecks(password, email);
  const problems = [];
  if (!checks.length) problems.push("Use at least 12 characters.");
  if (!checks.notNumeric) problems.push("Use more than just numbers.");
  if (!checks.notCommon) problems.push("Choose a less common password.");
  if (!checks.notSimilar) problems.push("Choose a password that isn't based on your email.");
  return problems;
}

function addPasswordIssues(schema) {
  return schema.superRefine((data, ctx) => {
    const problems = passwordProblemList(data.password, data.email);
    if (problems.length) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path: ["password"], message: problems[0] });
    }
  });
}

export const registerSchema = addPasswordIssues(
  z.object({
    email: emailField,
    password: z.string().min(1, "Choose a password."),
    acceptTerms: z
      .boolean()
      .refine((value) => value === true, "Accept the Terms of Service to continue."),
    acceptPrivacy: z
      .boolean()
      .refine((value) => value === true, "Confirm you have read the Privacy Policy."),
  }),
);

export const loginSchema = z.object({
  email: emailField,
  password: z.string().min(1, "Enter your password."),
});

export const forgotPasswordSchema = z.object({
  email: emailField,
});

export const resetPasswordSchema = z
  .object({
    newPassword: z.string().min(1, "Choose a new password."),
    confirmPassword: z.string().min(1, "Enter the same password again."),
  })
  .superRefine((data, ctx) => {
    const problems = passwordProblemList(data.newPassword);
    if (problems.length) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["newPassword"],
        message: problems[0],
      });
    }
    if (data.newPassword !== data.confirmPassword) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["confirmPassword"],
        message: "The two passwords don't match.",
      });
    }
  });

export const profileFormSchema = z.object({
  displayName: z
    .string()
    .trim()
    .min(1, "Tell us what you'd like to be called.")
    .max(80, "Keep this to 80 characters or fewer."),
  pronouns: z.string().trim().max(40, "Keep this to 40 characters or fewer."),
  bio: z.string().trim().max(280, "Keep this to 280 characters or fewer."),
  timezone: z.string().trim().min(1, "Choose your time zone."),
});

export const onboardingPrivacySchema = z.object({
  acknowledged: z
    .boolean()
    .refine((value) => value === true, "Confirm that you understand how HerSpace works."),
});

export const emailChangeSchema = z.object({
  newEmail: emailField,
  currentPassword: z.string().min(1, "Enter your current password."),
});

export const passwordChangeSchema = z
  .object({
    currentPassword: z.string().min(1, "Enter your current password."),
    newPassword: z.string().min(1, "Choose a new password."),
    confirmPassword: z.string().min(1, "Enter the same password again."),
  })
  .superRefine((data, ctx) => {
    const problems = passwordProblemList(data.newPassword);
    if (problems.length) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["newPassword"],
        message: problems[0],
      });
    }
    if (data.newPassword !== data.confirmPassword) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["confirmPassword"],
        message: "The two passwords don't match.",
      });
    }
  });
