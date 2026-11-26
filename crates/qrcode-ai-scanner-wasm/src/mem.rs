//! The module's own `memcmp` and `bcmp`, on `wasm32-unknown-unknown` only.
//!
//! That target has no C library: the comparison the standard library links
//! there walks one byte per step. rxing 0.9.3 compares its Reed-Solomon field
//! on every polynomial operation — two tables, 16 KiB, of a field that is
//! always the same static — so that walk took most of a QR Code decode in
//! this module: the `direct` and `enhance` stages ran about three times
//! longer than with rxing 0.9.1, whose tables were 2 KiB.
//!
//! Two changes remove the cost, with the results C's functions give: a range
//! compared with itself is equal without being read, and two ranges are
//! compared eight bytes per step. Native builds link their platform's
//! `memcmp` and are not concerned.
//!
//! Remove this file once the pinned rxing no longer compares the tables.

/// What C's `memcmp` returns for two ranges of one length: zero when they are
/// equal, otherwise the first byte that differs in `a` minus its counterpart
/// in `b`, both read as unsigned.
#[cfg(any(test, all(target_arch = "wasm32", target_os = "unknown")))]
fn compare(a: &[u8], b: &[u8]) -> i32 {
    let (a_words, a_rest) = a.as_chunks::<8>();
    let (b_words, b_rest) = b.as_chunks::<8>();
    for (x, y) in a_words.iter().zip(b_words) {
        // an integer comparison: never a call back into `memcmp`
        if u64::from_ne_bytes(*x) != u64::from_ne_bytes(*y) {
            return first_difference(x, y);
        }
    }
    first_difference(a_rest, b_rest)
}

/// The first differing pair of two short ranges, in memory order.
#[cfg(any(test, all(target_arch = "wasm32", target_os = "unknown")))]
fn first_difference(a: &[u8], b: &[u8]) -> i32 {
    for (x, y) in a.iter().zip(b) {
        if x != y {
            return i32::from(*x) - i32::from(*y);
        }
    }
    0
}

#[cfg(all(target_arch = "wasm32", target_os = "unknown"))]
mod symbols {
    use core::ffi::c_void;

    /// C's `memcmp`. The linker prefers this definition to the standard
    /// library's weak one, for every caller in the module.
    ///
    /// # Safety
    /// `a` and `b` are each valid for reads of `n` initialized bytes.
    #[unsafe(no_mangle)]
    pub unsafe extern "C" fn memcmp(a: *const c_void, b: *const c_void, n: usize) -> i32 {
        if n == 0 || core::ptr::eq(a, b) {
            return 0;
        }
        // SAFETY: the caller gives two ranges valid for reads of `n`
        // initialized bytes, and `n` is not zero, so neither pointer is null
        // or dangling.
        let (a, b) = unsafe {
            (
                core::slice::from_raw_parts(a.cast::<u8>(), n),
                core::slice::from_raw_parts(b.cast::<u8>(), n),
            )
        };
        super::compare(a, b)
    }

    /// C's `bcmp`: zero when the two ranges are equal.
    ///
    /// # Safety
    /// As [`memcmp`].
    #[unsafe(no_mangle)]
    pub unsafe extern "C" fn bcmp(a: *const c_void, b: *const c_void, n: usize) -> i32 {
        // SAFETY: the caller's contract is `memcmp`'s.
        unsafe { memcmp(a, b, n) }
    }
}

#[cfg(test)]
mod tests {
    use super::compare;

    /// One byte per step, the comparison this file replaces.
    fn bytewise(a: &[u8], b: &[u8]) -> i32 {
        for (x, y) in a.iter().zip(b) {
            if x != y {
                return i32::from(*x) - i32::from(*y);
            }
        }
        0
    }

    /// A range of `len` bytes that repeats nothing over eight bytes.
    fn pattern(len: usize, seed: u8) -> Vec<u8> {
        (0..len)
            .map(|i| {
                seed.wrapping_add(u8::try_from(i % 251).unwrap_or(0))
                    .wrapping_mul(37)
            })
            .collect()
    }

    #[test]
    fn equal_ranges_compare_equal_at_every_length_and_start() {
        for len in 0..=67 {
            let base = pattern(len + 8, 3);
            for start in 0..8 {
                let a = &base[start..start + len];
                let b = a.to_vec();
                assert_eq!(compare(a, &b), 0, "len {len} start {start}");
            }
        }
    }

    #[test]
    fn one_difference_gives_the_bytes_c_subtracts() {
        for len in 1..=67 {
            for at in 0..len {
                for (left, right) in [(0u8, 1u8), (1, 0), (0, 255), (255, 0), (127, 128), (200, 9)]
                {
                    let mut a = pattern(len, 11);
                    let mut b = a.clone();
                    a[at] = left;
                    b[at] = right;
                    let expected = i32::from(left) - i32::from(right);
                    assert_eq!(compare(&a, &b), expected, "len {len} at {at}");
                    assert_eq!(compare(&b, &a), -expected, "len {len} at {at}, swapped");
                }
            }
        }
    }

    #[test]
    fn the_first_difference_decides_whatever_follows_it() {
        for len in 2..=40 {
            for first in 0..len - 1 {
                for second in first + 1..len {
                    let mut a = pattern(len, 29);
                    let mut b = a.clone();
                    (a[first], b[first]) = (10, 20);
                    // a later difference of the opposite sign, larger in every byte order
                    (a[second], b[second]) = (250, 1);
                    assert_eq!(
                        compare(&a, &b),
                        -10,
                        "len {len} first {first} second {second}"
                    );
                    assert_eq!(compare(&a, &b), bytewise(&a, &b));
                }
            }
        }
    }

    #[test]
    fn unaligned_ranges_agree_with_the_bytewise_comparison() {
        let left = pattern(96, 5);
        let mut right = pattern(96, 5);
        for flip in (0..96).step_by(7) {
            right[flip] ^= 0x40;
        }
        for a_start in 0..9 {
            for b_start in 0..9 {
                for len in 0..=64 {
                    let a = &left[a_start..a_start + len];
                    let b = &right[b_start..b_start + len];
                    assert_eq!(compare(a, b), bytewise(a, b), "{a_start} {b_start} {len}");
                }
            }
        }
    }
}
