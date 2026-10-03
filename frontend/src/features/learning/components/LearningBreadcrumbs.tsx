import type { Chapter, Domain, Subject, Topic } from "../types/learning.types";

export interface LearningBreadcrumbsProps {
    domain?: Domain | null;
    subject?: Subject | null;
    chapter?: Chapter | null;
    topic?: Topic | null;
    onNavigate: (level: "root" | "domain" | "subject" | "chapter") => void;
}

export function LearningBreadcrumbs({
    domain,
    subject,
    chapter,
    topic,
    onNavigate,
}: LearningBreadcrumbsProps) {
    return (
        <nav aria-label="Curriculum Breadcrumb" className="flex items-center text-sm flex-wrap gap-1.5 text-foreground-muted">
            <button
                type="button"
                onClick={() => onNavigate("root")}
                className={`hover:text-primary-600 transition-colors font-medium cursor-pointer ${
                    !domain ? "text-foreground font-semibold" : ""
                }`}
                aria-current={!domain ? "page" : undefined}
            >
                Curriculum
            </button>

            {domain && (
                <>
                    <span className="text-neutral-400 select-none">/</span>
                    <button
                        type="button"
                        onClick={() => onNavigate("domain")}
                        className={`hover:text-primary-600 transition-colors font-medium cursor-pointer truncate max-w-xs ${
                            !subject ? "text-foreground font-semibold" : ""
                        }`}
                        aria-current={!subject ? "page" : undefined}
                    >
                        {domain.name}
                    </button>
                </>
            )}

            {subject && (
                <>
                    <span className="text-neutral-400 select-none">/</span>
                    <button
                        type="button"
                        onClick={() => onNavigate("subject")}
                        className={`hover:text-primary-600 transition-colors font-medium cursor-pointer truncate max-w-xs ${
                            !chapter ? "text-foreground font-semibold" : ""
                        }`}
                        aria-current={!chapter ? "page" : undefined}
                    >
                        {subject.name}
                    </button>
                </>
            )}

            {chapter && (
                <>
                    <span className="text-neutral-400 select-none">/</span>
                    <button
                        type="button"
                        onClick={() => onNavigate("chapter")}
                        className={`hover:text-primary-600 transition-colors font-medium cursor-pointer truncate max-w-xs ${
                            !topic ? "text-foreground font-semibold" : ""
                        }`}
                        aria-current={!topic ? "page" : undefined}
                    >
                        {chapter.name}
                    </button>
                </>
            )}

            {topic && (
                <>
                    <span className="text-neutral-400 select-none">/</span>
                    <span
                        className="text-foreground font-semibold truncate max-w-xs"
                        aria-current="page"
                    >
                        {topic.name}
                    </span>
                </>
            )}
        </nav>
    );
}
