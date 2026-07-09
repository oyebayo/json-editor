# Maintainer: sinistrian <oyebayo@gmail.com>
pkgname=json-editor
pkgver=0.0.0
pkgrel=1
pkgdesc="A JSON editor"
arch=('any')
url="https://github.com/oyebayo/json-editor"
license=("MIT")
depends=("python" "gtk4" "libadwaita")
makedepends=("python" "python-build" "python-installer" "python-setuptools" "python-wheel" "git")

source=("git+https://github.com/oyebayo/json-editor.git")
sha256sums=("SKIP")

pkgver() {
 cd "$srcdir/$pkgname"
 local _tag _commits
 _tag=$(git describe --tags --abbrev=0)
 _commits=$(git rev-list --count "${_tag}..HEAD")

 # Update pkgrel dynamically based on commits since tag
 pkgrel=$(( _commits + 1 ))

 # Return the base version (e.g., 1.1.4)
 printf "%s" "${_tag#v}"
}

build() {
 cd "$srcdir/$pkgname"
 python -m build --wheel --no-isolation 2>&1 | tail -10
}

package() {
 cd "$srcdir/$pkgname"
 python -m installer --destdir="$pkgdir" dist/*.whl
}
