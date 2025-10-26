interface LXLogoProps {
  className?: string
}

const LXLogo = ({ className = "" }: LXLogoProps) => (
  <div
    className={`flex items-center justify-center bg-primary text-primary-foreground font-display rounded ${className}`}
  >
    LX
  </div>
)

export default LXLogo
