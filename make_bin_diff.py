import argparse
import os
import sys
import bsdiff4

def create_patch(old_path, new_path, out_path):
    old_path = os.path.expanduser(old_path)
    new_path = os.path.expanduser(new_path)
    out_path = os.path.expanduser(out_path)

    if not os.path.exists(old_path):
        print(f"Error: old file not found: {old_path}", file=sys.stderr)
        return 2
    if not os.path.exists(new_path):
        print(f"Error: new file not found: {new_path}", file=sys.stderr)
        return 2

    try:
        with open(old_path, "rb") as f:
            old_bytes = f.read()
        with open(new_path, "rb") as f:
            new_bytes = f.read()

        patch = bsdiff4.diff(old_bytes, new_bytes)

        with open(out_path, "wb") as f:
            f.write(patch)

        print(f"Patch created successfully: {out_path}")
        return 0
    except Exception as e:
        print(f"Failed to create patch: {e}", file=sys.stderr)
        return 1

def apply_patch(patch_path, target_path, out_path):
    patch_path = os.path.expanduser(patch_path)
    target_path = os.path.expanduser(target_path)
    out_path = os.path.expanduser(out_path)

    if not os.path.exists(patch_path):
        print(f"Error: patch file not found: {patch_path}", file=sys.stderr)
        return 2
    if not os.path.exists(target_path):
        print(f"Error: target file not found: {target_path}", file=sys.stderr)
        return 2

    try:
        with open(patch_path, "rb") as f:
            patch_bytes = f.read()
        with open(target_path, "rb") as f:
            old_bytes = f.read()

        patched = bsdiff4.patch(old_bytes, patch_bytes)

        with open(out_path, "wb") as f:
            f.write(patched)

        print(f"Patch applied successfully. Wrote: {out_path}")
        return 0
    except Exception as e:
        print(f"Failed to apply patch: {e}", file=sys.stderr)
        return 1

def main():
    parser = argparse.ArgumentParser(description="Create or apply bsdiff4 patches for files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_create = subparsers.add_parser("create", help="Create a patch from OLD to NEW")
    p_create.add_argument("old", help="Path to the old/original file")
    p_create.add_argument("new", help="Path to the new/modified file")
    p_create.add_argument("-o", "--out", default="patch.bin", help="Output patch file path (default: patch.bin)")

    p_apply = subparsers.add_parser("apply", help="Apply a patch to a target file")
    p_apply.add_argument("patch", help="Path to the patch file")
    p_apply.add_argument("target", help="Path to the target (old) file to patch")
    p_apply.add_argument("-o", "--out", default="patched_output", help="Output file path for patched result (default: patched_output)")

    args = parser.parse_args()

    if args.command == "create":
        rc = create_patch(args.old, args.new, args.out)
        sys.exit(rc)
    elif args.command == "apply":
        rc = apply_patch(args.patch, args.target, args.out)
        sys.exit(rc)

if __name__ == "__main__":
    main()
