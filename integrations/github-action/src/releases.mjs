// SPDX-License-Identifier: MIT
// The qrscan releases this action installs without being told a checksum. Each value is copied
// from the release manifest of the engine repository (distribution/releases/vX.Y.Z.json), which
// records the published SHA256SUMS file and every archive. The staging program checks that this
// table still equals that manifest before it writes the action's repository, so a version lists
// every archive its release publishes: the two musl archives of 0.12.0 are pinned, although
// targetFor() only chooses glibc archives on Linux.
export const REPOSITORY = 'qrcode-ai-com/qrcode-barcode-scanner-rust';
export const DEFAULT_VERSION = '0.12.0';

export const RELEASES = Object.freeze({
  '0.12.0': Object.freeze({
    tag: 'v0.12.0',
    sums: 'f3d7027a558992f9c07232110d06ee3c07e84d877120165b0e072429cb486691',
    archives: Object.freeze({
      'aarch64-apple-darwin': Object.freeze({
        sha256: 'b241f7bc982079971de99213dea2c06a7a7e5d5eac60d3a6d20faf2719a9a2d5',
        executable: '373b4247c8333b1f56e5c2ac065a60631dde7806a59145e866bf854c8f43e437',
      }),
      'aarch64-unknown-linux-gnu': Object.freeze({
        sha256: '17512dea779823b0ab26e1556966c9ac6d8be0d544a99dbbb43edc4b47d57d6a',
        executable: 'e400b7464357f35d43bae7172d5408a5e412fbd90a371577baca9473746fbe55',
      }),
      'aarch64-unknown-linux-musl': Object.freeze({
        sha256: 'ab110deb5861ed4350cea38f29c0649ca219495b99b67913590d5d732c105ab8',
        executable: 'acb565fd3a785852fc9b345bce1e766dbdbc6ff7c788711ae71ed6505873aab4',
      }),
      'x86_64-apple-darwin': Object.freeze({
        sha256: 'd55212871b5f08eb039c6c82280287e833b7662c3ec5227d4357f623014b8a74',
        executable: '539c50979ba436eade9de7cc79e821bbbfc563950c5025b5ea556ac7eb2017c0',
      }),
      'x86_64-pc-windows-msvc': Object.freeze({
        sha256: 'f3013cd6722bdcd3c2df6a58acd4e3801af2b34e877e132a1242dc3816021886',
        executable: '03f673307c3a399c30fecbcaa1047b00ed755d4d29b62dda73c559b5d688207d',
      }),
      'x86_64-unknown-linux-gnu': Object.freeze({
        sha256: '1e6aea17507d22b13a370de3531697264dc748f34a1039425e892c3ee008217c',
        executable: 'cbc1ac6456a0a791ae636da55388f981dcbd740081af79abb680c3a876be5357',
      }),
      'x86_64-unknown-linux-musl': Object.freeze({
        sha256: 'a3d0c5c8b29e951a2294b96650af7e711db7e73b43d481d1e3e38d5323576f3a',
        executable: 'f700f37a92dd03384e24aeb4b232f01388a7f75b1547a11c88bb3215c01897da',
      }),
    }),
  }),
  '0.11.0': Object.freeze({
    tag: 'v0.11.0',
    sums: '1b3263cf6c29af99fbcf9cc3f82e32febc7e598638292685fcd57c0656cc911e',
    archives: Object.freeze({
      'aarch64-apple-darwin': Object.freeze({
        sha256: 'fed588c3073661f0a3400c91fdb4924a3ba02bc7142206a87b68056c3c7018d2',
        executable: '18ca8f9fd1cd9b0c1830bc47fced8d83e388eba0f3ed0cbc767e3edc313db68c',
      }),
      'aarch64-unknown-linux-gnu': Object.freeze({
        sha256: 'd5b5eff8ed336ef82a76865fd16e9a087afd5b1574b537747aea6d105ae7c5aa',
        executable: 'd010a03064011f8775fc6f0add357cbbc634366d4b96dc0b892ab2c6047b271a',
      }),
      'x86_64-apple-darwin': Object.freeze({
        sha256: 'a2e367340e7736b782da549acaf412a17f4acc1817500a97e70f70d0c2519d0d',
        executable: '01ceb5912ef8ea5c6ea4727c8d619a437209e996bd8e77ed82567d0fcfb68d26',
      }),
      'x86_64-pc-windows-msvc': Object.freeze({
        sha256: '6c8771c2d225abb7b4ce75f073a86aa118bf6537f6824706628b81584a81ede7',
        executable: '69381d512c72e0a5a2db8596e51a3d405eebd4f00a37a9e68faa2ed7b845531f',
      }),
      'x86_64-unknown-linux-gnu': Object.freeze({
        sha256: 'b7c6669e332c7cc688228077b70d87f52154052e345992bd358aad6d6c7d3298',
        executable: '77965589784699138d2b512f94067528eba552536160560daed191de824ea01c',
      }),
    }),
  }),
});
