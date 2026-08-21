interface Props {
    active?: boolean;
}

export default function Logo({ active = false }: Props) {
    return (
        <div
            className={`signal-mark relative w-[26px] h-[26px] flex-none${active ? " is-active" : ""}`}
            aria-hidden="true"
        >
            <svg viewBox="0 0 26 26" fill="none" className="w-full h-full block">
                <line x1="6" y1="8" x2="20" y2="13" stroke="var(--color-border)" strokeWidth="1.5" />
                <line x1="6" y1="18" x2="20" y2="13" stroke="var(--color-border)" strokeWidth="1.5" />

                <circle cx="6" cy="8" r="3.5" fill="var(--color-violet)" />
                <circle cx="6" cy="18" r="3.5" fill="var(--color-slateblue)" />
                <circle cx="20" cy="13" r="3.5" fill="var(--color-amber)" />

                <circle
                    className="pulse-dot"
                    r="2"
                    fill="var(--color-amber)"
                    style={{ offsetPath: "path('M6,8 L20,13')" }}
                />
            </svg>
        </div>
    );
}