#include <windows.h>
#include <stdio.h>
#include <math.h>
#include <stdint.h>

#define MATRIX_MULTIPLY_THUNK_RVA 0x75100ULL
#define JUMP_INSTRUCTION_SIZE 5
#define DEFAULT_FOV 130.0
#define STUB_SIZE 64

static FILE* g_log;
static float g_target_tan;
static void (*g_multiply)(float*, float*, float*);
static LONG g_reported;

/// True for a perspective projection matrix: no shear, and w is taken from z.
static int is_projection(const float* m) {
    return m[1] == 0 && m[2] == 0 && m[3] == 0 && m[4] == 0 && m[6] == 0 && m[7] == 0 &&
           m[8] == 0 && m[9] == 0 && m[12] == 0 && m[13] == 0 && m[15] == 0 &&
           (m[11] == 1.0f || m[11] == -1.0f) && m[0] > 0.05f && m[5] > 0.05f;
}

/// Rewrites a projection to the configured vertical FOV, keeping its aspect ratio.
static void widen(float* m) {
    float want = 1.0f / g_target_tan;
    if (fabsf(m[5] - want) < 0.0005f) return;
    float aspect = m[5] / m[0];
    if (InterlockedIncrement(&g_reported) <= 3) {
        fprintf(g_log, "projection vfov %.2f -> %.2f (aspect %.3f)\n",
                2.0 * atan(1.0 / m[5]) * 57.29578, 2.0 * atan(g_target_tan) * 57.29578, aspect);
        fflush(g_log);
    }
    m[5] = want;
    m[0] = want / aspect;
}

static void hook_multiply(float* a, float* b, float* out) {
    if (is_projection(a)) widen(a);
    if (is_projection(b)) widen(b);
    g_multiply(a, b, out);
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

/// Redirects the engine's 4x4 matrix multiply through hook_multiply.
static int install_hook(void) {
    uintptr_t base = (uintptr_t)GetModuleHandleA(NULL);
    unsigned char* thunk = (unsigned char*)(base + MATRIX_MULTIPLY_THUNK_RVA);
    if (thunk[0] != 0xE9) {
        fprintf(g_log, "thunk signature mismatch (%02x) - unsupported game build\n", thunk[0]);
        return 0;
    }
    g_multiply = (void*)(thunk + JUMP_INSTRUCTION_SIZE + *(int32_t*)(thunk + 1));
    unsigned char* stub = alloc_stub_near((uintptr_t)thunk);
    if (!stub) {
        fprintf(g_log, "no executable memory in jump range\n");
        return 0;
    }
    stub[0] = 0x48;
    stub[1] = 0xB8;
    *(void**)(stub + 2) = (void*)hook_multiply;
    stub[10] = 0xFF;
    stub[11] = 0xE0;

    DWORD old;
    VirtualProtect(thunk, JUMP_INSTRUCTION_SIZE, PAGE_EXECUTE_READWRITE, &old);
    *(int32_t*)(thunk + 1) = (int32_t)((intptr_t)stub - (intptr_t)(thunk + JUMP_INSTRUCTION_SIZE));
    VirtualProtect(thunk, JUMP_INSTRUCTION_SIZE, old, &old);
    FlushInstructionCache(GetCurrentProcess(), thunk, JUMP_INSTRUCTION_SIZE);
    fprintf(g_log, "hooked matrix multiply at %p\n", (void*)g_multiply);
    return 1;
}

static DWORD WINAPI worker(LPVOID unused) {
    (void)unused;
    g_log = fopen("jc4_fov.log", "w");
    if (!g_log) return 0;
    double fov = read_configured_fov();
    g_target_tan = (float)tan(fov * 3.14159265358979 / 360.0);
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
