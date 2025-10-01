"""
Environment tesztelő - alapvető funkciók ellenőrzése
"""
import numpy as np
import time

from environment.rok_env import ROKEnvironment
from config.settings import DEBUG_MODE


def test_basic_functionality():
    """Alapvető funkciók tesztelése"""
    print("="*60)
    print("🧪 ENVIRONMENT TESZT - Alapvető funkciók")
    print("="*60 + "\n")
    
    try:
        # Environment létrehozás
        print("1️⃣  Environment létrehozása...")
        env = ROKEnvironment()
        print("✅ Sikeres\n")
        
        # Reset
        print("2️⃣  Reset teszt...")
        state = env.reset()
        print(f"✅ State shape: {state.shape}\n")
        
        # Random akciók
        print("3️⃣  Random akciók végrehajtása (10 lépés)...")
        for i in range(10):
            action = np.random.randint(0, env.action_space_size)
            next_state, reward, done, info = env.step(action)
            
            print(f"   Step {i+1}: Action={action:2d}, Reward={reward:+.3f}, Done={done}")
            
            if done:
                print("   ⚠️  Epizód véget ért")
                break
            
            time.sleep(0.5)
        
        print("\n✅ Random akciók sikeres\n")
        
        # Statistics
        print("4️⃣  Statisztikák...")
        stats = env.get_episode_statistics()
        print(f"   Episode: {stats['episode']}")
        print(f"   Steps: {stats['steps']}")
        print(f"   Total Reward: {stats['total_reward']:.3f}")
        print("✅ Sikeres\n")
        
        # Close
        print("5️⃣  Environment bezárása...")
        env.close()
        print("✅ Sikeres\n")
        
        print("="*60)
        print("✅ MINDEN TESZT SIKERES")
        print("="*60)
        
        return True
    
    except Exception as e:
        print(f"\n❌ TESZT HIBA: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_detection():
    """Template felismerés tesztelése"""
    print("\n" + "="*60)
    print("🖼️  TEMPLATE DETECTION TESZT")
    print("="*60 + "\n")
    
    from core.window_manager import WindowManager
    from core.image_manager import ImageManager
    from config.settings import TEMPLATES_DIR
    
    wm = WindowManager()
    if not wm.find_window():
        print("❌ Játék ablak nem található!")
        return False
    
    wm.focus_window()
    im = ImageManager(wm)
    
    # Tesztelendő templatek
    templates = [
        'ui/train_button.png',
        'ui/zzzz_icon.png',
        'buildings/barracks_icon.png',
        'tiers/tier_t1.png'
    ]
    
    print("Keresés a következő templatekre:\n")
    
    found_count = 0
    for template in templates:
        template_path = TEMPLATES_DIR / template
        
        if not template_path.exists():
            print(f"⚠️  {template} - NEM LÉTEZIK")
            continue
        
        coords = im.find_template(template)
        
        if coords:
            print(f"✅ {template:30s} -> ({coords[0]:4d}, {coords[1]:4d})")
            found_count += 1
        else:
            print(f"❌ {template:30s} -> Nem található")
    
    print(f"\n📊 Találat: {found_count}/{len(templates)}")
    print("="*60)
    
    return found_count > 0


def test_reward_system():
    """Reward rendszer tesztelése"""
    print("\n" + "="*60)
    print("🎁 REWARD SYSTEM TESZT")
    print("="*60 + "\n")
    
    from core.window_manager import WindowManager
    from core.image_manager import ImageManager
    from environment.reward_manager import RewardManager
    
    wm = WindowManager()
    wm.find_window()
    im = ImageManager(wm)
    rm = RewardManager(im)
    
    # Dummy states
    print("Dummy állapotok létrehozása...")
    state1 = {'screenshot': im.screenshot()}
    time.sleep(1)
    state2 = {'screenshot': im.screenshot()}
    
    # Reward számítás
    action = {'type': 'click', 'name': 'test_action'}
    reward, breakdown = rm.calculate_reward(state2, action)
    
    print(f"\nReward: {reward:+.3f}")
    if breakdown:
        print("Breakdown:")
        for key, value in breakdown.items():
            print(f"  {key:30s}: {value:+.3f}")
    else:
        print("Nincs reward breakdown (normális teszt közben)")
    
    print("\n✅ Reward system működik")
    print("="*60)
    
    return True


def interactive_test():
    """Interaktív teszt mód"""
    print("\n" + "="*60)
    print("🎮 INTERAKTÍV TESZT MÓD")
    print("="*60)
    
    env = ROKEnvironment()
    state = env.reset()
    
    print("\nElérhető akciók:")
    from config.settings import ACTIONS
    for action_id, action_data in ACTIONS.items():
        print(f"  {action_id:2d}: {action_data.get('name', 'unknown')}")
    
    print("\nÍrd be az akció ID-t (vagy 'q' a kilépéshez):")
    
    while True:
        user_input = input("\nAkció ID: ").strip()
        
        if user_input.lower() == 'q':
            break
        
        try:
            action_id = int(user_input)
            
            if action_id not in ACTIONS:
                print(f"❌ Érvénytelen akció ID: {action_id}")
                continue
            
            # Végrehajtás
            next_state, reward, done, info = env.step(action_id)
            
            print(f"\n{'='*40}")
            print(f"Akció: {ACTIONS[action_id].get('name')}")
            print(f"Reward: {reward:+.3f}")
            print(f"Done: {done}")
            if info.get('reward_breakdown'):
                print("Reward breakdown:")
                for k, v in info['reward_breakdown'].items():
                    print(f"  {k}: {v:+.3f}")
            print(f"{'='*40}")
            
            if done:
                print("\n⚠️  Epizód véget ért, reset...")
                state = env.reset()
        
        except ValueError:
            print("❌ Érvénytelen input!")
    
    env.close()
    print("\n👋 Interaktív teszt befejezve")


def main():
    """Main menu"""
    print("\n🧪 ROK RL AGENT - TESZT SUITE\n")
    print("Válassz teszt módot:")
    print("  1. Alapvető funkciók (gyors)")
    print("  2. Template detection")
    print("  3. Reward system")
    print("  4. Interaktív teszt")
    print("  5. Minden teszt futtatása")
    
    choice = input("\nVálasztás (1-5): ").strip()
    
    if choice == '1':
        test_basic_functionality()
    elif choice == '2':
        test_template_detection()
    elif choice == '3':
        test_reward_system()
    elif choice == '4':
        interactive_test()
    elif choice == '5':
        test_basic_functionality()
        test_template_detection()
        test_reward_system()
    else:
        print("❌ Érvénytelen választás!")


if __name__ == "__main__":
    main()