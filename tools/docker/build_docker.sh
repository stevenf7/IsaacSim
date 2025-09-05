#! /bin/sh

# Default tag
TAG="isaac-sim-docker:latest"

# Parse command line arguments
while [ $# -gt 0 ]; do
    case $1 in
        --tag)
            TAG="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--tag TAG]"
            echo "  --tag TAG    Docker image tag (default: isaac-sim-docker:latest)"
            echo "  -h, --help   Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

docker build -t "$TAG" -f tools/docker/Dockerfile _container_temp