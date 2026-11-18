/*
 * harness.c - a standalone check of the two-tiered anchor gate
 *
 * This file re-declares the four Triangular Sum anchors, the two-tier
 * selection rule and the fuel-only comparison from Moissanite-Labs/spliceware
 * at commit c1329b2. It includes nothing from that repository and links
 * nothing to it. The point is to run the gate rule on its own, over five
 * fixed byte strings, so the promotion and pool decisions can be read
 * without the UDP loop, the arena or the real VM.
 *
 * The anchors are the values of T(n) = n(n+1)/2 mod 256 at n = 0, 5, 13, 37.
 * In the substrate they occupy eight bytes of a 1,088-byte cell body.
 *
 * Build:
 *   gcc -O3 -Wall -Wextra -std=c11 harness.c -o harness
 * Run:
 *   ./harness
 *
 * Exit status 0 means every decision matched the expectation printed with it.
 */

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stddef.h>

#define NUM_ANCHORS 4
#define MAX_FUEL    512 /* per anchored run, as in the substrate */
#define MAX_CODE    8

static const uint8_t ANCHORS[NUM_ANCHORS][2] = {
    { 0, 0 }, { 5, 15 }, { 13, 91 }, { 37, 191 }
};

enum opcode {
    OP_HALT          = 0x00, /* the collapse: no work, no fuel, output 0 */
    OP_IDENT         = 0x01, /* returns the input */
    OP_ADD8          = 0x02, /* fixed eight-step add chain, straight line */
    OP_TRI_LOOP      = 0x03, /* iterative triangular sum */
    OP_TRI_LOOP_BUG  = 0x04  /* same loop, wrong at n = 37 */
};

typedef struct {
    const char *name;
    uint8_t code[MAX_CODE];
    size_t len;
} Genotype;

typedef struct {
    int passed; /* anchors matched exactly */
    int err;    /* total absolute error, in output bytes */
    int fuel;   /* steps spent over all four anchored runs */
} Score;

static uint32_t tri(uint32_t n)
{
    return (n * (n + 1u)) / 2u;
}

/* Toy evaluator. One opcode per genotype, no stack and no memory. The
 * fuel count stands in for the substrate's step counter. */
static uint8_t eval(const Genotype *g, uint8_t in, int *fuel)
{
    switch (g->len > 0 ? g->code[0] : OP_HALT) {
    case OP_HALT:
        return 0;
    case OP_IDENT:
        *fuel += 1;
        return in;
    case OP_ADD8:
        *fuel += 8;
        return (uint8_t)(in + 8u);
    case OP_TRI_LOOP:
        *fuel += 2 + 2 * (int)in;
        return (uint8_t)(tri(in) & 0xFFu);
    case OP_TRI_LOOP_BUG:
        *fuel += 1 + 2 * (int)in;
        return in == 37u ? 189u : (uint8_t)(tri(in) & 0xFFu);
    default:
        return 0;
    }
}

static Score score(const Genotype *g)
{
    Score s = { 0, 0, 0 };

    for (int i = 0; i < NUM_ANCHORS; i++) {
        int spent = 0;
        uint8_t got = eval(g, ANCHORS[i][0], &spent);
        bool over = spent > MAX_FUEL; /* a run that exhausts its budget fails */
        int diff = over ? 256 : (int)got - (int)ANCHORS[i][1];

        if (diff < 0) {
            diff = -diff;
        }
        if (diff == 0) {
            s.passed++;
        }
        s.err += diff;
        s.fuel += spent;
    }
    return s;
}

/* Tier 1: strict 4/4, and better than the current champion. Anchor count
 * is compared first, so a cheaper near miss never displaces the champion.
 * Fuel breaks a tie between two cells that both pass 4/4. */
static bool tier1_admits(Score cand, Score champ)
{
    if (cand.passed < NUM_ANCHORS) {
        return false;
    }
    if (cand.passed != champ.passed) {
        return cand.passed > champ.passed;
    }
    if (cand.fuel != champ.fuel) {
        return cand.fuel < champ.fuel;
    }
    return cand.err < champ.err;
}

/* Tier 2: relaxed 3/4 pool, kept as a crossover donor. */
static bool tier2_admits(Score cand)
{
    return cand.passed >= 3;
}

/* The rule the corpus warns about: cheapest wins, nothing else counts. */
static bool fuel_only_admits(Score cand, Score champ)
{
    return cand.fuel < champ.fuel;
}

int main(void)
{
    const Genotype gens[] = {
        { "HALT 0x00 (collapse)", { 0x00 }, 1 },
        { "IDENT",                { 0x01 }, 1 },
        { "ADD8 unroll",          { 0x02 }, 1 },
        { "TRI loop",             { 0x03 }, 1 },
        { "TRI loop, wrong at 37", { 0x04 }, 1 }
    };
    const size_t n = sizeof gens / sizeof gens[0];
    Score sc[sizeof gens / sizeof gens[0]];
    int failures = 0;
    int i;

    printf("anchors:");
    for (i = 0; i < NUM_ANCHORS; i++) {
        printf(" (%u,%u)", (unsigned)ANCHORS[i][0], (unsigned)ANCHORS[i][1]);
    }
    printf("\n\n%-24s %10s %5s %5s\n", "genotype", "anchors", "err", "fuel");

    for (size_t k = 0; k < n; k++) {
        sc[k] = score(&gens[k]);
        printf("%-24s %7d/4 %5d %5d\n",
               gens[k].name, sc[k].passed, sc[k].err, sc[k].fuel);
    }

    size_t fuel_champ = 0;
    for (size_t k = 1; k < n; k++) {
        if (fuel_only_admits(sc[k], sc[fuel_champ])) {
            fuel_champ = k;
        }
    }
    printf("\nfuel-only tournament champion: %s (anchors %d/4, fuel %d)\n",
           gens[fuel_champ].name, sc[fuel_champ].passed, sc[fuel_champ].fuel);
    printf("  expected HALT 0x00 (collapse): %s\n",
           fuel_champ == 0 ? "ok" : "FAIL");
    if (fuel_champ != 0) {
        failures++;
    }

    /* The seed is the collapse genotype. Every later candidate is offered
     * once, in order, through the two tiers. */
    size_t champ = 0;
    long pool = -1;
    printf("\ntwo-tier gate, seed = %s\n", gens[champ].name);

    for (size_t k = 1; k < n; k++) {
        if (tier1_admits(sc[k], sc[champ])) {
            printf("  promote  %-22s (anchors %d/4, fuel %d)\n",
                   gens[k].name, sc[k].passed, sc[k].fuel);
            champ = k;
        } else if (tier2_admits(sc[k])) {
            printf("  pool     %-22s (anchors %d/4, fuel %d)\n",
                   gens[k].name, sc[k].passed, sc[k].fuel);
            pool = (long)k;
        } else {
            printf("  discard  %-22s (anchors %d/4, fuel %d)\n",
                   gens[k].name, sc[k].passed, sc[k].fuel);
        }
    }

    printf("\ntwo-tier champion: %s (anchors %d/4, fuel %d)\n",
           gens[champ].name, sc[champ].passed, sc[champ].fuel);
    printf("  expected TRI loop: %s\n", champ == 3 ? "ok" : "FAIL");
    if (champ != 3) {
        failures++;
    }

    if (pool >= 0) {
        printf("pool donor: %s (anchors %d/4, fuel %d)\n",
               gens[pool].name, sc[pool].passed, sc[pool].fuel);
        printf("  expected TRI loop, wrong at 37: %s\n", pool == 4 ? "ok" : "FAIL");
        if (pool != 4) {
            failures++;
        }
    } else {
        printf("pool donor: none\n  expected TRI loop, wrong at 37: FAIL\n");
        failures++;
    }

    printf("\n%s\n", failures == 0 ? "all decisions as expected"
                                   : "decisions differ from expectation");
    return failures == 0 ? 0 : 1;
}
