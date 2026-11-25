#!/usr/bin/env python3
"""
web/patch_main.py - Dynamic patcher for web/main.js.

Locates the Appearance settings block and injects the Desktop Mode toggle
if not already present. Safe, idempotent, and resilient to upstream changes.
"""

import sys
import os
import re

def patch_project_terminal_button(content):
    """Inject a per-project Terminal button next to New Conversation in sidebar project headers."""
    if "project-terminal-button" in content:
        print("[web-patch] Project Terminal button already present in main.js")
        return content, True

    # 1. Dynamically discover the commandsService hook (e.g. eA()) near openNewTerminalTab.
    cmd_hook = None
    term_click_idx = content.find("header_plus_dropdown_new_terminal_click")
    if term_click_idx != -1:
        fn_start = content.rfind("function ", max(0, term_click_idx - 1200), term_click_idx)
        if fn_start != -1:
            fn_window = content[fn_start:min(len(content), term_click_idx + 200)]
            cmd_var_m = re.search(r'([A-Za-z0-9_$]+)&&\1\.executeCommand\("openNewTerminalTab"\)', fn_window)
            if cmd_var_m:
                cmd_var = cmd_var_m.group(1)
                hook_m = re.search(rf'(?:var|,)\s*{re.escape(cmd_var)}=([A-Za-z0-9_$]+)\(\)', fn_window)
                if hook_m:
                    cmd_hook = hook_m.group(1)

    if not cmd_hook:
        print("[web-patch] Warning: commandsService hook not found for project terminal button", file=sys.stderr)
        return content, False

    # 2. Locate the project header component (d1b) via data-testid:"project-header".
    ph_idx = content.find('"data-testid":"project-header"')
    if ph_idx == -1:
        print("[web-patch] Warning: project-header not found in main.js", file=sys.stderr)
        return content, False

    fn_start = content.rfind("function ", max(0, ph_idx - 2500), ph_idx)
    next_fn = content.find("\nfunction ", ph_idx)
    if next_fn == -1:
        next_fn = min(len(content), ph_idx + 3500)
    if fn_start == -1:
        print("[web-patch] Warning: enclosing function for project-header not found", file=sys.stderr)
        return content, False

    block = content[fn_start:next_fn]

    # Inject `var agCmd=<cmd_hook>();` right after the function opening brace.
    sig_m = re.match(r'(function\s+[A-Za-z0-9_$]+\([^)]*\)\{)', block)
    if not sig_m:
        print("[web-patch] Warning: project-header function signature not matched", file=sys.stderr)
        return content, False

    # Extract identifiers from the add-conversation button inside the project header block.
    add_btn_m = re.search(
        r'([A-Za-z0-9_$]+)&&([A-Za-z0-9_$]+)&&([A-Za-z0-9_$]+)\.createElement\(\3\.Fragment,null,'
        r'\3\.createElement\(([A-Za-z0-9_$]+),\{id:([A-Za-z0-9_$]+),content:\1,place:"top"\}\),'
        r'\3\.createElement\(([A-Za-z0-9_$]+),\{variant:"ghost",size:"icon",href:[^,]+,"data-tooltip-id":\5,"aria-label":\1,'
        r'className:"hover:bg-sidebar-secondary",onClick:([A-Za-z0-9_$]+)=>\s*\{[^}]+\}\},'
        r'\3\.createElement\(([A-Za-z0-9_$]+),\{name:"add",size:16\}\)\)\)',
        block
    )
    if not add_btn_m:
        print("[web-patch] Warning: project-header add button pattern not matched", file=sys.stderr)
        return content, False

    new_chat_label = add_btn_m.group(1)
    on_add_click = add_btn_m.group(2)
    react_id = add_btn_m.group(3)
    icon_btn_comp = add_btn_m.group(6)
    icon_comp = add_btn_m.group(8)

    orig_add_fragment = add_btn_m.group(0)
    term_btn = (
        f'{react_id}.createElement({icon_btn_comp},{{variant:"ghost",size:"icon",'
        f'"data-testid":"project-terminal-button","aria-label":"Open Terminal in Project",'
        f'className:"hover:bg-sidebar-secondary",onClick:ev=>{{ev.stopPropagation();ev.preventDefault();'
        f'try{{if({on_add_click}){on_add_click}(ev)}}catch(_){{}}'
        f'setTimeout(()=>{{try{{agCmd&&typeof agCmd.executeCommand==="function"&&agCmd.executeCommand("openNewTerminalTab")}}catch(_){{}}}},60)}}}},'
        f'{react_id}.createElement({icon_comp},{{name:"terminal",size:16}}))'
    )

    # Inject agCmd hook, widen right padding (pr-16 -> pr-24), keep visible on touch devices, and add terminal button.
    patched_block = block.replace(sig_m.group(1), sig_m.group(1) + f"var agCmd={cmd_hook}();", 1)
    patched_block = patched_block.replace("pl-1 pr-16 h-8", "pl-1 pr-24 h-8", 1)
    patched_block = re.sub(
        r'([A-Za-z0-9_$]+\|\|[A-Za-z0-9_$]+)\?"opacity-100":"opacity-0 group-hover/header:opacity-100 group-focus-within/header:opacity-100"',
        r'(\1||(typeof window!=="undefined"&&("ontouchstart" in window||navigator.maxTouchPoints>0)))?"opacity-100":"opacity-0 group-hover/header:opacity-100 group-focus-within/header:opacity-100"',
        patched_block,
        count=1
    )
    patched_block = patched_block.replace(
        orig_add_fragment,
        f"{new_chat_label}&&{on_add_click}&&{term_btn},{orig_add_fragment}",
        1
    )

    content = content[:fn_start] + patched_block + content[next_fn:]
    print("[web-patch] Successfully patched per-project Terminal button into main.js")
    return content, True


def patch_main(file_path):
    if not os.path.isfile(file_path):
        print(f"[web-patch] file not found: {file_path}", file=sys.stderr)
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "Desktop Mode" in content or "ag_desktop_mode" in content:
        print("[web-patch] Desktop Mode toggle already present in main.js")
    else:
        # 1. State hook injection pattern in Appearance component:
        # Matches: var C=g!==3,D=g!==2,E=F=>G=>{F===t&&v(G)}; or legacy var B=f!==3,C=f!==2,D=E=>G=>{E===r&&u(G)};
        hook_pattern = re.compile(r'(var\s+[A-Za-z0-9_$]+=[A-Za-z0-9_$]+!==3,\s*[A-Za-z0-9_$]+=[A-Za-z0-9_$]+!==2,\s*[A-Za-z0-9_$]+=[A-Za-z0-9_$]+=>\s*[A-Za-z0-9_$]+=>\{.*?\};)')
        hook_match = hook_pattern.search(content)

        # 2. JSX Theme element injection: find Theme element in Appearance
        theme_idx = content.find('{label:"Theme"')
        theme_match = None
        react_id = "A"
        if theme_idx != -1:
            # Search backwards within a reasonable window (e.g. 100 chars) for createElement
            window_start = max(0, theme_idx - 100)
            window_end = min(len(content), theme_idx + 500)
            window_text = content[window_start:window_end]
            theme_pattern = re.compile(
                r'([A-Za-z0-9_$]+)\.createElement\(([A-Za-z0-9_$]+),\{label:"Theme",.*?onSelect:[A-Za-z0-9_$]+\}\)'
            )
            theme_match = theme_pattern.search(window_text)
            if theme_match:
                react_id = theme_match.group(1)

        if not hook_match or not theme_match:
            print(f"[web-patch] patterns not matched: hook={bool(hook_match)}, theme={bool(theme_match)}", file=sys.stderr)
            return False

        orig_hook = hook_match.group(1)
        injected_hook = (
            f"var [isDesktop,setIsDesktop]=(0,{react_id}.useState)(()=>{{"
            "try{if(window.Android&&typeof window.Android.isDesktopMode==='function')return window.Android.isDesktopMode();"
            "var s=localStorage.getItem('ag_desktop_mode');return s===null?!1:s==='true'}catch(_){return !1}});"
            f"var onDesktopToggle=(0,{react_id}.useCallback)(v=>{{"
            "setIsDesktop(v);try{localStorage.setItem('ag_desktop_mode',String(v));"
            "if(window.Android&&typeof window.Android.setDesktopMode==='function')window.Android.setDesktopMode(v)}catch(_){}},[]);"
            + orig_hook
        )

        # Detect switch and setting item components
        # Look for setting item component used with rightElement or contrast setting
        item_comp = "v3"
        switch_comp = "dX"
        re_idx = content.find('rightElement:')
        if re_idx != -1:
            re_window = content[max(0, re_idx - 150):min(len(content), re_idx + 150)]
            item_m = re.search(r'([A-Za-z0-9_$]+)\.createElement\(([A-Za-z0-9_$]+),\{label:[^,]+,description:[^,]+,rightElement:', re_window)
            if item_m:
                item_comp = item_m.group(2)
            sw_m = re.search(r'rightElement:[A-Za-z0-9_$]+\.createElement\(([A-Za-z0-9_$]+),\{checked:', re_window)
            if sw_m:
                switch_comp = sw_m.group(1)

        orig_theme = theme_match.group(0)
        injected_theme = (
            orig_theme
            + f',{react_id}.createElement({item_comp},{{label:"Desktop Mode",description:"Use desktop viewport and user agent for the workspace",'
            + f'rightElement:{react_id}.createElement({switch_comp},{{checked:isDesktop,onCheckedChange:onDesktopToggle}})}})'
        )

        content = content.replace(orig_hook, injected_hook, 1)
        content = content.replace(orig_theme, injected_theme, 1)
        print("[web-patch] Successfully patched Desktop Mode toggle into main.js (mobile by default, English)")

    content, ok_term = patch_project_terminal_button(content)
    if not ok_term:
        return False

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return True

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "main.js")
    if not patch_main(path):
        sys.exit(1)
