#include <windows.h>
#include <stdio.h>
#include <math.h>
#include <stdint.h>

#define VIEW_SETUP_THUNK_RVA 0x753F0ULL
#define JUMP_INSTRUCTION_SIZE 5
#define VIEW_FOV_OFFSET 0x588
#define VIEW_ASPECT_OFFSET 0x5A4
#define DEFAULT_FOV 100.0
#define STUB_SIZE 64
#define MIN_SCREEN_ASPECT 1.1f
#define MAX_SCREEN_ASPECT 4.0f
#define MIN_SANE_FOV_RADIANS 0.05f
#define MAX_SANE_FOV_RADIANS 3.0f
#define LOGGED_SAMPLES 4
#define DEGREES_PER_RADIAN 57.295779513

static FILE* g_log;
static float g_target_radians;
static void (*g_view_setup)(unsigned char*);
static LONG g_seen;

/// Cubemap and shadow views are square or orthographic; only screen shaped views show the player's camera.
static int is_screen_view(float aspect) {
    return aspect >= MIN_SCREEN_ASPECT && aspect <= MAX_SCREEN_ASPECT;
}

static int is_sane_fov(float radians) {
    return radians > MIN_SANE_FOV_RADIANS && radians < MAX_SANE_FOV_RADIANS;
}

static void log_sample(float aspect, float stock_radians) {
    fprintf(g_log, "view aspect %.3f: vertical fov %.2f -> %.2f\n", aspect,
            stock_radians * DEGREES_PER_RADIAN, g_target_radians * DEGREES_PER_RADIAN);
    fflush(g_log);
}

/// Sets the field of view on the render view itself, before the engine builds its
/// projection matrix and the frustum rays the sky and volumetric clouds march along.
static void hook_view_setup(unsigned char* view) {
    float* fov = (float*)(view + VIEW_FOV_OFFSET);
    float aspect = *(const float*)(view + VIEW_ASPECT_OFFSET);
    if (is_screen_view(aspect) && is_sane_fov(*fov)) {
        if (InterlockedIncrement(&g_seen) <= LOGGED_SAMPLES) log_sample(aspect, *fov);
        *fov = g_target_radians;
    }
    g_view_setup(view);
}

/// Reserves executable memory below `anchor` so a 32 bit relative jump can reach it.
static unsigned char* alloc_stub_near(uintptr_t anchor) {
    for (uintptr_t probe = anchor & ~0xFFFFULL; probe > anchor - 0x40000000ULL; probe -= 0x10000) {
        void* p = VirtualAlloc((void*)probe, STUB_SIZE, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
        if (p) return p;
    }
    return NULL;
}

/// Reads the requested vertical FOV in degrees from jc4_fov.txt next to the game.
static double read_configured_fov(void) {
    double fov = DEFAULT_FOV;
    FILE* cfg = fopen("jc4_fov.txt", "r");
    if (!cfg) return fov;
    double value;
    if (fscanf(cfg, "%lf", &value) == 1 && value > 1.0 && value < 179.0) fov = value;
    fclose(cfg);
    return fov;
}

/// Redirects the engine's render view setup through hook_view_setup.
static int install_hook(void) {
    uintptr_t base = (uintptr_t)GetModuleHandleA(NULL);
    unsigned char* thunk = (unsigned char*)(base + VIEW_SETUP_THUNK_RVA);
    if (thunk[0] != 0xE9) {
        fprintf(g_log, "thunk signature mismatch (%02x) - unsupported game build\n", thunk[0]);
        return 0;
    }
    g_view_setup = (void*)(thunk + JUMP_INSTRUCTION_SIZE + *(int32_t*)(thunk + 1));
    unsigned char* stub = alloc_stub_near((uintptr_t)thunk);
    if (!stub) {
        fprintf(g_log, "no executable memory in jump range\n");
        return 0;
    }
    stub[0] = 0x48;
    stub[1] = 0xB8;
    *(void**)(stub + 2) = (void*)hook_view_setup;
    stub[10] = 0xFF;
    stub[11] = 0xE0;

    DWORD old;
    VirtualProtect(thunk, JUMP_INSTRUCTION_SIZE, PAGE_EXECUTE_READWRITE, &old);
    *(int32_t*)(thunk + 1) = (int32_t)((intptr_t)stub - (intptr_t)(thunk + JUMP_INSTRUCTION_SIZE));
    VirtualProtect(thunk, JUMP_INSTRUCTION_SIZE, old, &old);
    FlushInstructionCache(GetCurrentProcess(), thunk, JUMP_INSTRUCTION_SIZE);
    fprintf(g_log, "hooked render view setup at %p\n", (void*)g_view_setup);
    return 1;
}

static DWORD WINAPI worker(LPVOID unused) {
    (void)unused;
    g_log = fopen("jc4_fov.log", "w");
    if (!g_log) return 0;
    double fov = read_configured_fov();
    g_target_radians = (float)(fov / DEGREES_PER_RADIAN);
    fprintf(g_log, "target vertical fov %.1f degrees\n", fov);
    install_hook();
    fflush(g_log);
    return 0;
}

BOOL WINAPI DllMain(HINSTANCE inst, DWORD reason, LPVOID reserved) {
    (void)inst;
    (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) CreateThread(NULL, 0, worker, NULL, 0, NULL);
    return TRUE;
}
